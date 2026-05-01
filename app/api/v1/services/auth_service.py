from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.dependencies import DBSession
from app.api.v1.repositories import user_repo, auth_repo
from app.schemas.custom_schema import Token


async def login(db:DBSession,user_data:OAuth2PasswordRequestForm):
    user = await user_repo.get_user_by_email(db,user_data.username)

    if not user:
        raise HTTPException(
            status_code=409,
            detail="Esse endereço de email não foi encontrado no servidor!, verifique se digitou corretamente"
        )
    
    if not user or not auth_repo.verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail='Email ou senha incorretos!, verifique se digitou corretamente.'
        )
    
    access_token = auth_repo.create_token(data={'sub':f'{user.email}'})

    token = Token(access_token=access_token, token_type='Bearer')

    return token