from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.services import auth_service, user_service
from app.schemas.custom_schema import LoginSuccess
from app.schemas.user_schema import UserCreate, UserPublic, UserUpdate

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
        key='Login_info',
        value=token.access_token,
        max_age=60 * 60,
        httponly=True,
        secure=False,
        samesite='lax',
    )

    response.headers['Cache-Control'] = 'no-store'

    return {'status': 'success', 'user': user_info}


@user_route.post('/logout',status_code=HTTPStatus.OK, response_model=str)
async def user_logout(user:CurrentUser, response: Response):
    response.delete_cookie('Login_info')
    return 'Usuário deslogado.'


@user_route.get(
    '/users', status_code=HTTPStatus.OK, response_model=List[UserPublic]
)
async def users(db: DBSession, user: CurrentUser):
    return await user_service.get_users(db, user)


@user_route.get(
    '/users/{id_user}', status_code=HTTPStatus.OK, response_model=UserPublic
)
async def user(db: DBSession, r: rediscon, user: CurrentUser, id_user: int):
    return await user_service.get_user(db, r, user, id_user)


@user_route.put('/users', status_code=HTTPStatus.OK, response_model=UserPublic)
async def uptade_user(
    db: DBSession,
    r: rediscon,
    user: CurrentUser,
    user_data: UserUpdate,
    response: Response,
):
    update = await user_service.update_user_data(db, r, user, user_data)

    response.delete_cookie('Login_info')

    return update


@user_route.delete('/users', status_code=HTTPStatus.NO_CONTENT)
async def delete_user(
    db: DBSession, user: CurrentUser, r: rediscon, response: Response
):
    await user_service.delete_user(db, user, r)
    response.delete_cookie('Login_info')
