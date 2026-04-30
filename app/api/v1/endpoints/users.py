from http import HTTPStatus

from fastapi import APIRouter
from app.api.v1.dependencies import DBSession
from app.api.v1.services import user_service
from app.schemas.user_schema import UserCreate, UserPublic


user_route = APIRouter()


@user_route.post('/users',status_code=HTTPStatus.CREATED, response_model=UserPublic)
async def user_create(db:DBSession, user_data:UserCreate):
    return await user_service.create_user_service(db, user_data)
