from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.services import appoint_service, auth_service, user_service
from app.core.config import settings
from app.redis.limiter import limiter
from app.schemas.appointment_schema import AppointmentUserResponse
from app.schemas.custom_schema import LoginSuccess
from app.schemas.user_schema import UserCreate, UserPublic, UserUpdate

user_route = APIRouter()
Form_data = Annotated[OAuth2PasswordRequestForm, Depends()]


@user_route.post('/users', status_code=HTTPStatus.CREATED, response_model=UserPublic)
@limiter.limit('10/hour')
async def user_create(request: Request, db: DBSession, user_data: UserCreate):
    return await user_service.create_user_service(db, user_data)


@user_route.post('/login', status_code=HTTPStatus.OK, response_model=LoginSuccess)
@limiter.limit('5/minute')
async def login_user(
    request: Request, db: DBSession, user: Form_data, response: Response
):
    token, user_info = await auth_service.login(db, user)

    response.set_cookie(
        key='Login_info',
        value=token.access_token,
        max_age=60 * 60,
        httponly=True,
        secure=settings.ENV == 'production',
        path='/',
        samesite='none' if settings.ENV == 'production' else 'lax',
    )

    response.headers['Cache-Control'] = 'no-store'

    return {'status': 'success', 'user': user_info}


@user_route.post('/logout', status_code=HTTPStatus.OK, response_model=str)
async def user_logout(user: CurrentUser, response: Response):
    response.delete_cookie(
        key='Login_info',
        path='/',
        httponly=True,
        secure=settings.ENV == 'production',
        samesite='none' if settings.ENV == 'production' else 'lax',
    )
    return 'Usuário deslogado.'


@user_route.get('/users', status_code=HTTPStatus.OK, response_model=List[UserPublic])
@limiter.limit('3/minute')
async def users(request: Request, db: DBSession, user: CurrentUser):
    return await user_service.get_users(db, user)


@user_route.get(
    '/users/{id_user}', status_code=HTTPStatus.OK, response_model=UserPublic
)
@limiter.limit('3/minute')
async def user(
    request: Request, db: DBSession, r: rediscon, user: CurrentUser, id_user: int
):
    return await user_service.get_user(db, r, user, id_user)


@user_route.put('/users', status_code=HTTPStatus.OK, response_model=UserPublic)
@limiter.limit('3/minute')
async def uptade_user(  # noqa
    request: Request,
    db: DBSession,
    r: rediscon,
    user: CurrentUser,
    user_data: UserUpdate,
    response: Response,
):
    update = await user_service.update_user_data(db, r, user, user_data)

    response.delete_cookie(
        key='Login_info',
        path='/',
        httponly=True,
        secure=settings.ENV == 'production',
        samesite='none' if settings.ENV == 'production' else 'lax',
    )

    return update


@user_route.delete('/users', status_code=HTTPStatus.NO_CONTENT)
async def desactive_user(
    db: DBSession, user: CurrentUser, r: rediscon, response: Response
):
    await user_service.desactive_account(db, user, r)
    response.delete_cookie(
        key='Login_info',
        path='/',
        httponly=True,
        secure=settings.ENV == 'production',
        samesite='none' if settings.ENV == 'production' else 'lax',
    )


@user_route.get(
    '/users/me/appointments',
    status_code=HTTPStatus.OK,
    response_model=List[AppointmentUserResponse],
)
@limiter.limit('6/minute')
async def get_all_appointments(request: Request, db: DBSession, user: CurrentUser):
    return await appoint_service.get_user_appointment(db, user)


@user_route.get(
    '/users/me/next-appointments',
    status_code=HTTPStatus.OK,
    response_model=List[AppointmentUserResponse] | dict,
)
@limiter.limit('6/minute')
async def next_appoinments(request: Request, db: DBSession, user: CurrentUser):
    return await user_service.get_next_appoiments(db, user)


@user_route.post(
    '/validate-session', status_code=HTTPStatus.OK, response_model=LoginSuccess
)
@limiter.limit('6/minute')
async def validate_cookie(request: Request, user: CurrentUser):
    user_info = {
        'email': f'{user.email}',
        'fullname': f'{user.fullname}',
        'role': f'{user.role}',
    }

    return {'status': 'success', 'user': user_info}


@user_route.get(
    '/users/me/open-appoiments',
    status_code=HTTPStatus.OK,
    response_model=List[AppointmentUserResponse] | dict,
)
@limiter.limit('10/minute')
async def open_appoiments(db: DBSession, user: CurrentUser):
    return await user_service.get_open_appoiments(db, user)
