from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.dependencies import DBSession
from app.api.v1.services import auth_service, user_service
from app.schemas.custom_schema import Token
from app.schemas.user_schema import UserCreate, UserPublic

user_route = APIRouter()
Form_data = Annotated[OAuth2PasswordRequestForm, Depends()]


@user_route.post(
    '/users', status_code=HTTPStatus.CREATED, response_model=UserPublic
)
async def user_create(db: DBSession, user_data: UserCreate):
    return await user_service.create_user_service(db, user_data)


@user_route.post('/login', status_code=HTTPStatus.OK, response_model=Token)
async def login_user(db: DBSession, user: Form_data):
    return await auth_service.login(db, user)
