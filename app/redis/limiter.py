import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings


def client_ip(request: Request) -> str:
    """IP real do cliente, sem se deixar enganar por X-Forwarded-For forjado.

    Atrás de proxy (Render, Cloudflare...), `request.client.host` é o IP do PROXY:
    todos os usuários cairiam no mesmo balde de rate limit (um atacante esgotaria o
    limite de login de TODO mundo). Por outro lado, confiar no X-Forwarded-For
    inteiro deixa o cliente escolher o próprio IP. O correto é contar a partir da
    DIREITA: cada proxy confiável acrescenta o IP que viu ao final do cabeçalho.

    TRUSTED_PROXY_HOPS = quantos proxies confiáveis existem na frente da aplicação
    (0 = nenhum: usa o IP do socket).
    """
    hops = settings.TRUSTED_PROXY_HOPS

    if hops > 0:
        forwarded = request.headers.get('x-forwarded-for', '')
        parts = [part.strip() for part in forwarded.split(',') if part.strip()]

        if len(parts) >= hops:
            return parts[-hops]

    return get_remote_address(request)


def _token_from(request: Request) -> str | None:
    token = request.cookies.get('Login_info')

    if token:
        return token

    header = request.headers.get('authorization', '')

    if header.startswith('Bearer '):
        return header.split(' ', 1)[1]

    return None


def user_or_ip_key(request: Request) -> str:
    """Chave por USUÁRIO autenticado (assinatura verificada); senão, por IP.

    Limita por pessoa e não por IP: vários pacientes atrás do mesmo NAT não se
    atrapalham, e quem troca de IP não escapa do limite.
    """
    token = _token_from(request)

    if token:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={'require': ['exp', 'sub']},
            )
            return f'user:{payload["sub"]}'
        except jwt.PyJWTError:
            pass

    return f'ip:{client_ip(request)}'


limiter = Limiter(
    key_func=client_ip,
    storage_uri=f'{settings.REDIS_URL}',
    enabled=not settings.TESTING,
)
