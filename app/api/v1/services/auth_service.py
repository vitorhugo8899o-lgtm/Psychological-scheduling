from typing import TYPE_CHECKING

import jwt
from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr, TypeAdapter, ValidationError

from app.api.v1.repositories import auth_repo, user_repo
from app.core.config import Settings
from app.models.users_models import User
from app.schemas.custom_schema import Token

if TYPE_CHECKING:
    from app.api.v1.dependencies import DBSession

settings = Settings()

email_validator = TypeAdapter(EmailStr)


async def login(
    db: DBSession, user_data: OAuth2PasswordRequestForm
) -> tuple[Token, User]:

    try:
        email_validator.validate_python(user_data.username)
    except ValidationError:
        raise HTTPException(
            status_code=422, detail='O formato do e-mail enviado é inválido.'
        )

    user = await user_repo.get_user_by_email(db, user_data.username)

    if not user:
        raise HTTPException(
            status_code=409,
            detail=(
                'Esse endereço de email não foi encontrado no servidor!'
                ',verifique se digitou corretamente'
            ),
        )

    if not user or not auth_repo.verify_password(
        user_data.password, user.password
    ):
        raise HTTPException(
            status_code=401,
            detail=(
                'Email ou senha incorretos!, verifique se digitou corretamente'
            ),
        )

    access_token = auth_repo.create_token(data={'sub': f'{user.email}'})

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


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        user_email: str = payload.get('sub')

        if user_email is None:
            raise HTTPException(status_code=401, detail='Token inválido')

        return user_email

    except (jwt.PyJWTError, ValueError) as e:
        raise HTTPException(
            status_code=401, detail=f'Token inválido ou expirado {e}'
        )
