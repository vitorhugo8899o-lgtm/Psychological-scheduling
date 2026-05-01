from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.dependencies import DBSession
from app.api.v1.services import auth_service, user_service
from app.schemas.custom_schema import LoginSuccess
from app.schemas.user_schema import UserCreate, UserPublic

user_route = APIRouter()
Form_data = Annotated[OAuth2PasswordRequestForm, Depends()]


@user_route.post(
    '/users', status_code=HTTPStatus.CREATED, response_model=UserPublic
)
async def user_create(db: DBSession, user_data: UserCreate):
    return await user_service.create_user_service(db, user_data)


@user_route.post(
        '/login', status_code=HTTPStatus.OK, response_model=LoginSuccess
)
async def login_user(db: DBSession, user: Form_data, response: Response):
    token, user_info = await auth_service.login(db, user)

    response.set_cookie(
        key="Login_info",
        value=token.access_token,
        max_age=60 * 60,
        httponly=True,
        secure=False,
        samesite="none",
    )

    response.headers['Cache-Control'] = 'no-store'

    return {
        "status": "success",
        "user": user_info
    }
