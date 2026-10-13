"""Regressão: CSRF (Origin), cabeçalhos, docs e rate limit atrás de proxy."""

from http import HTTPStatus

import httpx
import jwt
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from app.api.v1.repositories import auth_repo
from app.core.config import settings
from app.main import allowed_origins, docs_kwargs
from app.redis.limiter import client_ip, user_or_ip_key

EVIL = 'https://evil.example'


@pytest.fixture(autouse=True)
def frozen_time():
    """Sobrescreve o freeze_time global deste módulo.

    O armazenamento em memória do rate limit expira chaves num thread (Timer) e o
    freezegun devolve a hora REAL para código chamado de `threading`: com o relógio
    congelado, as chaves expiravam em momentos aleatórios (teste intermitente).
    """
    return


FRONT = 'http://localhost:5173'  # permitido fora de produção
LOGOUT = '/api/v1/logout'


# --------------------------------------------------------------- CSRF / Origin


@pytest.mark.asyncio
async def test_cross_site_state_change_with_session_cookie_is_blocked(token_client):
    blocked = await token_client.post(LOGOUT, headers={'Origin': EVIL})

    assert blocked.status_code == HTTPStatus.FORBIDDEN
    assert blocked.json() == {'detail': 'Origem não autorizada.'}

    # a sessão NÃO foi derrubada pelo site malicioso
    still_logged = await token_client.get('/api/v1/services')
    assert still_logged.status_code == HTTPStatus.OK


@pytest.mark.asyncio
@pytest.mark.parametrize('origin', [EVIL, 'null', 'http://localhost:5173.evil.com'])
async def test_unknown_origins_are_blocked(token_client, origin):
    response = await token_client.post(LOGOUT, headers={'Origin': origin})

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_referer_is_used_when_origin_is_missing(token_client):
    evil = await token_client.post(LOGOUT, headers={'Referer': f'{EVIL}/pagina'})
    assert evil.status_code == HTTPStatus.FORBIDDEN

    front = await token_client.post(LOGOUT, headers={'Referer': f'{FRONT}/consultas'})
    assert front.status_code == HTTPStatus.OK


@pytest.mark.asyncio
@pytest.mark.parametrize('origin', [FRONT, 'http://test', None])
async def test_front_end_same_origin_and_non_browser_clients_still_work(
    token_client, origin
):
    headers = {'Origin': origin} if origin else {}

    response = await token_client.post(LOGOUT, headers=headers)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_login_csrf_from_another_site_is_blocked(client, user_client):
    response = await client.post(
        '/api/v1/login',
        data={'username': 'user@example.com', 'password': 'Senha12@#'},
        headers={'Origin': EVIL},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert 'Login_info' not in response.cookies


@pytest.mark.asyncio
async def test_safe_methods_are_not_affected_by_the_origin_guard(token_client):
    response = await token_client.get('/api/v1/services', headers={'Origin': EVIL})

    assert response.status_code == HTTPStatus.OK  # (o CORS impede o site de ler)


@pytest.mark.asyncio
async def test_cors_preflight_only_for_the_front_end(client):
    ok = await client.options(
        LOGOUT,
        headers={'Origin': FRONT, 'Access-Control-Request-Method': 'POST'},
    )
    bad = await client.options(
        LOGOUT,
        headers={'Origin': EVIL, 'Access-Control-Request-Method': 'POST'},
    )

    assert ok.headers['access-control-allow-origin'] == FRONT
    assert 'access-control-allow-origin' not in bad.headers


def test_allowed_origins_exclude_localhost_in_production(monkeypatch):
    monkeypatch.setattr(settings, 'ENV', 'production')

    assert not any('localhost' in origin for origin in allowed_origins())


def test_allowed_origins_can_be_configured_by_environment(monkeypatch):
    monkeypatch.setattr(
        settings, 'CORS_ORIGINS', 'https://app.clinica.com/, https://b.com'
    )

    assert allowed_origins() == ['https://app.clinica.com', 'https://b.com']


# ---------------------------------------------------------- cabeçalhos e /docs


@pytest.mark.asyncio
async def test_api_responses_carry_security_headers(token_client):
    response = await token_client.get('/api/v1/services')

    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-frame-options'] == 'DENY'
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert 'strict-transport-security' not in response.headers  # só em produção


@pytest.mark.asyncio
async def test_hsts_is_sent_in_production(token_client, monkeypatch):
    monkeypatch.setattr(settings, 'ENV', 'production')

    response = await token_client.get('/api/v1/services')

    assert 'max-age=31536000' in response.headers['strict-transport-security']


def test_api_docs_are_disabled_in_production_unless_explicitly_enabled(monkeypatch):
    monkeypatch.setattr(settings, 'ENV', 'production')
    monkeypatch.setattr(settings, 'ENABLE_DOCS', False)
    assert docs_kwargs() == {
        'docs_url': None,
        'redoc_url': None,
        'openapi_url': None,
    }

    monkeypatch.setattr(settings, 'ENABLE_DOCS', True)
    assert docs_kwargs() == {}

    monkeypatch.setattr(settings, 'ENV', 'development')
    monkeypatch.setattr(settings, 'ENABLE_DOCS', False)
    assert docs_kwargs() == {}


# ------------------------------------------------------- rate limit atrás de proxy


def _request(headers=None, client=('10.0.0.9', 5000)):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'query_string': b'',
        'headers': raw,
        'client': client,
    })


def test_forged_forwarded_for_is_ignored_without_trusted_proxy(monkeypatch):
    monkeypatch.setattr(settings, 'TRUSTED_PROXY_HOPS', 0)

    request = _request({'X-Forwarded-For': '1.2.3.4'})

    assert client_ip(request) == '10.0.0.9'


@pytest.mark.parametrize(
    ('hops', 'header', 'expected'),
    [
        (1, '203.0.113.7', '203.0.113.7'),
        (1, '9.9.9.9, 203.0.113.7', '203.0.113.7'),  # prefixo forjado é ignorado
        (2, '198.51.100.1, 203.0.113.7', '198.51.100.1'),
        (2, 'fake, 198.51.100.1, 203.0.113.7', '198.51.100.1'),
        (2, '203.0.113.7', '10.0.0.9'),  # menos entradas que proxies: IP do socket
        (1, '', '10.0.0.9'),
    ],
)
def test_client_ip_counts_from_the_right(monkeypatch, hops, header, expected):
    monkeypatch.setattr(settings, 'TRUSTED_PROXY_HOPS', hops)

    request = _request({'X-Forwarded-For': header} if header else {})

    assert client_ip(request) == expected


def test_user_key_uses_the_verified_token_subject():
    token = auth_repo.create_token({'sub': 'ana@example.com'})

    by_cookie = _request({'Cookie': f'Login_info={token}'})
    by_header = _request({'Authorization': f'Bearer {token}'})

    assert user_or_ip_key(by_cookie) == 'user:ana@example.com'
    assert user_or_ip_key(by_header) == 'user:ana@example.com'


def test_user_key_falls_back_to_ip_for_forged_or_missing_tokens():
    forged = jwt.encode(
        {'sub': 'vitima@example.com', 'exp': 9999999999}, 'outra', 'HS256'
    )

    assert user_or_ip_key(_request({'Cookie': f'Login_info={forged}'})) == 'ip:10.0.0.9'
    assert user_or_ip_key(_request()) == 'ip:10.0.0.9'


def _limited_app(key_func):
    limiter = Limiter(key_func=client_ip, storage_uri='memory://')
    app = FastAPI()
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def handler(request, exc):
        return JSONResponse(status_code=429, content={'detail': 'limite'})

    @app.get('/x')
    @limiter.limit('2/minute', key_func=key_func)
    async def route(request: Request):
        return {'ok': True}

    return app


async def _hit(app, ip, headers=None):
    transport = httpx.ASGITransport(app=app, client=(ip, 1))
    async with httpx.AsyncClient(transport=transport, base_url='http://t') as c:
        return (await c.get('/x', headers=headers)).status_code


@pytest.mark.asyncio
async def test_rate_limit_is_per_user_not_per_shared_ip():
    app = _limited_app(user_or_ip_key)
    ana = {'Authorization': 'Bearer ' + auth_repo.create_token({'sub': 'ana@x.com'})}
    bia = {'Authorization': 'Bearer ' + auth_repo.create_token({'sub': 'bia@x.com'})}

    assert [await _hit(app, '1.1.1.1', ana) for _ in range(3)] == [200, 200, 429]
    # a Ana trocando de IP continua limitada...
    assert await _hit(app, '2.2.2.2', ana) == HTTPStatus.TOO_MANY_REQUESTS
    # ...e a Bia, no MESMO IP da Ana, não é afetada
    assert await _hit(app, '1.1.1.1', bia) == HTTPStatus.OK


@pytest.mark.asyncio
async def test_rate_limit_behind_proxy_separates_real_clients(monkeypatch):
    monkeypatch.setattr(settings, 'TRUSTED_PROXY_HOPS', 1)
    app = _limited_app(client_ip)
    proxy = '10.0.0.1'  # todos chegam pelo mesmo proxy

    one = {'X-Forwarded-For': '203.0.113.1'}
    forged = {'X-Forwarded-For': '9.9.9.9, 203.0.113.1'}  # tenta se passar por outro
    two = {'X-Forwarded-For': '203.0.113.2'}

    assert await _hit(app, proxy, one) == HTTPStatus.OK
    assert await _hit(app, proxy, forged) == HTTPStatus.OK
    assert await _hit(app, proxy, one) == HTTPStatus.TOO_MANY_REQUESTS
    assert await _hit(app, proxy, two) == HTTPStatus.OK
