"""Testes de regressão das correções de sessão/autenticação (auditoria)."""

from http import HTTPStatus
from unittest.mock import patch

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings

LOGIN = '/api/v1/login'
PASSWORD = 'Senha12@#'
JTI_LENGTH = 32


async def _login(client, email='user@example.com', password=PASSWORD):
    return await client.post(LOGIN, data={'username': email, 'password': password})


def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


@pytest.mark.asyncio
async def test_token_carries_iat_jti_and_token_version(client, user_client):
    response = await _login(client)

    claims = jwt.decode(
        response.cookies['Login_info'],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    assert claims['sub'] == 'user@example.com'
    assert claims['tv'] == 0
    assert len(claims['jti']) == JTI_LENGTH
    assert 'iat' in claims
    assert 'exp' in claims


@pytest.mark.asyncio
async def test_token_without_expiration_is_rejected(client, user_client):
    forever = jwt.encode(
        {'sub': 'user@example.com'}, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    response = await client.get('/api/v1/services', headers=_bearer(forever))

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Token inválido'


@pytest.mark.asyncio
async def test_deactivated_account_token_stops_working(client, user_client):
    token = (await _login(client)).cookies['Login_info']

    ok = await client.get('/api/v1/services', headers=_bearer(token))
    assert ok.status_code == HTTPStatus.OK

    assert (await client.delete('/api/v1/users')).status_code == HTTPStatus.NO_CONTENT

    # O token copiado antes da desativação NÃO pode continuar valendo.
    client.cookies.clear()
    response = await client.get('/api/v1/services', headers=_bearer(token))

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == (
        'Sessão inválida ou expirada. Faça login novamente.'
    )


@pytest.mark.asyncio
async def test_password_change_invalidates_previous_tokens(client, user_client):
    old_token = (await _login(client)).cookies['Login_info']

    response = await client.put(
        '/api/v1/users',
        json={
            'email': 'user@example.com',
            'current_password': PASSWORD,
            'password': 'NovaSenha12@#',
        },
    )
    assert response.status_code == HTTPStatus.OK

    client.cookies.clear()
    stale = await client.get('/api/v1/services', headers=_bearer(old_token))
    assert stale.status_code == HTTPStatus.UNAUTHORIZED

    fresh = await _login(client, password='NovaSenha12@#')
    assert fresh.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_update_requires_the_current_password(token_client, user_client):
    response = await token_client.put(
        '/api/v1/users',
        json={
            'email': 'attacker@example.com',
            'current_password': 'SenhaErrada12@#',
            'password': 'Hackeada12@#',
        },
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()['detail'] == 'Senha atual incorreta.'

    # nada mudou: o login original continua funcionando
    assert (await _login(token_client)).status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_update_without_current_password_is_rejected(token_client):
    response = await token_client.put(
        '/api/v1/users',
        json={'email': 'attacker@example.com', 'password': 'Hackeada12@#'},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_logout_revokes_the_token_on_the_server(client, user_client, fake_redis):
    token = (await _login(client)).cookies['Login_info']

    ok = await client.get('/api/v1/services', headers=_bearer(token))
    assert ok.status_code == HTTPStatus.OK

    assert (await client.post('/api/v1/logout')).status_code == HTTPStatus.OK

    client.cookies.clear()
    response = await client.get('/api/v1/services', headers=_bearer(token))

    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_deactivated_account_is_indistinguishable_without_the_password(
    client, user_client, db_session
):
    user_client.is_active = False
    await db_session.commit()

    wrong = await _login(client, password='Errada12@#')
    unknown = await _login(client, email='ninguem@example.com')
    right = await _login(client)

    assert wrong.status_code == unknown.status_code == HTTPStatus.UNAUTHORIZED
    assert wrong.json() == unknown.json()
    # Só quem sabe a senha descobre que a conta está desativada.
    assert right.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_login_is_blocked_after_repeated_failures(
    client, user_client, fake_redis, monkeypatch
):
    monkeypatch.setattr(settings, 'LOGIN_MAX_FAILURES', 3)

    for _ in range(3):
        failed = await _login(client, password='Errada12@#')
        assert failed.status_code == HTTPStatus.UNAUTHORIZED

    # Mesmo com a senha correta, a conta fica temporariamente bloqueada.
    blocked = await _login(client)
    assert blocked.status_code == HTTPStatus.TOO_MANY_REQUESTS


@pytest.mark.asyncio
async def test_successful_login_clears_the_failure_counter(
    client, user_client, fake_redis, monkeypatch
):
    monkeypatch.setattr(settings, 'LOGIN_MAX_FAILURES', 3)

    for _ in range(2):
        await _login(client, password='Errada12@#')

    assert (await _login(client)).status_code == HTTPStatus.OK

    for _ in range(2):
        await _login(client, password='Errada12@#')

    assert (await _login(client)).status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_internal_errors_do_not_leak_to_the_client(client, db_session):
    payload = {
        'fullname': 'Nome Completo',
        'email': 'novo@example.com',
        'password': PASSWORD,
    }

    with patch.object(
        db_session, 'commit', side_effect=RuntimeError('INSERT INTO users SEGREDO-SQL')
    ):
        response = await client.post('/api/v1/users', json=payload)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert 'SEGREDO-SQL' not in response.text
    assert 'INSERT' not in response.text


def _settings(**overrides):
    base = {
        'DATABASE_URL': 'postgresql+asyncpg://u:p@localhost/db',
        'SECRET_KEY': 'x' * 48,
        'ACESSES_TOKEN_EXPIRE_MINUTES': 60,
        'ALGORITHM': 'HS256',
        'REDIS_URL': 'redis://localhost:6379/0',
        'API_KEY_MERCADO_PAGO': 'k',
        'ENV': 'production',
        'API_KEY_GROQ': 'k',
        'LINK_FRONTEND': 'https://front/',
        'SENTRY_DSN': '',
        'MERCADO_PAGO_SECRET': 's',
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


def test_settings_accept_a_strong_configuration():
    assert _settings().is_production is True


def test_settings_reject_weak_secret_in_production():
    with pytest.raises(ValidationError):
        _settings(SECRET_KEY='sua_chave')

    with pytest.raises(ValidationError):
        _settings(SECRET_KEY='curta')


def test_settings_allow_short_secret_outside_production():
    assert _settings(ENV='development', SECRET_KEY='curta').SECRET_KEY == 'curta'


@pytest.mark.parametrize('algorithm', ['none', 'RS256', 'ES256', ''])
def test_settings_reject_non_hmac_algorithms(algorithm):
    with pytest.raises(ValidationError):
        _settings(ALGORITHM=algorithm)
