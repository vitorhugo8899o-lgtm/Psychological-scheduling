import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings


def client_ip(request: Request) -> str:
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
