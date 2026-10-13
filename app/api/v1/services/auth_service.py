import hashlib
import logging
import time
from typing import TYPE_CHECKING

import jwt
from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr, TypeAdapter, ValidationError
from redis.exceptions import RedisError

from app.api.v1.repositories import auth_repo, user_repo
from app.core.config import settings
from app.models.users_models import User
from app.schemas.custom_schema import Token

if TYPE_CHECKING:
    from app.api.v1.dependencies import DBSession, rediscon

email_validator = TypeAdapter(EmailStr)

# Hash descartável: quando o e-mail não existe, ainda executamos uma verificação
# Argon2 para que o tempo de resposta não revele se a conta existe.
DUMMY_PASSWORD_HASH = auth_repo.hash_password('senha-descartavel-tempo-constante')

CLOCK_SKEW_LEEWAY_SECONDS = 10


def _login_failures_key(email: str) -> str:
    digest = hashlib.sha256(email.strip().lower().encode('utf-8')).hexdigest()
    return f'login_failures:{digest}'


async def _ensure_login_not_blocked(r: rediscon, key: str) -> None:
    try:
        failures = await r.get(key)
    except RedisError:
        logging.exception('[Auth] Redis indisponível ao checar bloqueio de login')
        return

    if failures and int(failures) >= settings.LOGIN_MAX_FAILURES:
        raise HTTPException(
            status_code=429,
            detail='Muitas tentativas de login. Tente novamente em alguns minutos.',
        )


async def _register_login_failure(r: rediscon, key: str) -> None:
    try:
        # SET NX EX cria o contador já com TTL (evita chave eterna se o processo cair
        # entre INCR e EXPIRE); INCR preserva o TTL.
        await r.set(key, 0, ex=settings.LOGIN_FAILURE_WINDOW_SECONDS, nx=True)
        await r.incr(key)
    except RedisError:
        logging.exception('[Auth] Redis indisponível ao registrar falha de login')


async def _clear_login_failures(r: rediscon, key: str) -> None:
    try:
        await r.delete(key)
    except RedisError:
        logging.exception('[Auth] Redis indisponível ao limpar falhas de login')


async def login(
    db: DBSession, user_data: OAuth2PasswordRequestForm, r: rediscon
) -> tuple[Token, User]:

    try:
        email_validator.validate_python(user_data.username)
    except ValidationError:
        raise HTTPException(
            status_code=422, detail='O formato do e-mail enviado é inválido.'
        )

    failures_key = _login_failures_key(user_data.username)
    await _ensure_login_not_blocked(r, failures_key)

    user = await user_repo.get_user_by_email(db, user_data.username)

    # A senha é SEMPRE verificada antes de qualquer outra checagem: assim "conta
    # inexistente", "senha errada" e "conta desativada" não são distinguíveis por
    # quem não conhece a senha (nem pelo tempo de resposta).
    password_ok = auth_repo.verify_password(
        user_data.password, user.password if user else DUMMY_PASSWORD_HASH
    )

    if not user or not password_ok:
        await _register_login_failure(r, failures_key)
        raise HTTPException(status_code=401, detail='Email ou senha incorretos!')

    if user.is_active is False:
        raise HTTPException(status_code=403, detail='Esta conta se encontra desativa.')

    await _clear_login_failures(r, failures_key)

    access_token = auth_repo.create_token(
        data={'sub': f'{user.email}', 'tv': user.token_version}
    )

    token = Token(access_token=access_token, token_type='Bearer')

    return token, user


def get_token(request: Request) -> str:
    token = None
    cookie_token = request.cookies.get('Login_info')

    if cookie_token:
        token = cookie_token
    else:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

    if not token:
        raise HTTPException(status_code=401, detail='Usuário não autenticado.')

    return token


def decode_token_payload(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            leeway=CLOCK_SKEW_LEEWAY_SECONDS,
            options={'require': ['exp', 'sub']},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expirado')
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail='Token inválido')

    if not payload.get('sub'):
        raise HTTPException(status_code=401, detail='Token inválido')

    return payload


def decode_token(token: str) -> str:
    return decode_token_payload(token)['sub']


def _revoked_key(jti: str) -> str:
    return f'revoked_jti:{jti}'


async def revoke_token(r: rediscon, payload: dict) -> None:
    """Revoga o jti do token até o momento em que ele expiraria."""
    jti = payload.get('jti')
    exp = payload.get('exp')

    if not jti or not exp:
        return

    ttl = max(int(exp - time.time()), 1)

    try:
        await r.set(_revoked_key(jti), '1', ex=ttl)
    except RedisError:
        logging.exception('[Auth] Redis indisponível ao revogar token')


async def is_token_revoked(r: rediscon, payload: dict) -> bool:
    jti = payload.get('jti')

    if not jti:
        return False

    try:
        return bool(await r.exists(_revoked_key(jti)))
    except RedisError:
        # Falha aberta: o token continua limitado por exp e por token_version.
        logging.exception('[Auth] Redis indisponível ao checar revogação de token')
        return False
