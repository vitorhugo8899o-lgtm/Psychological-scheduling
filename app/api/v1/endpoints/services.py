
from http import HTTPStatus
from typing import List
from app.schemas.service_schema import ServiceResponse
from app.api.v1.dependencies import DBSession, rediscon
from fastapi import APIRouter
from app.api.v1.services import user_service


service_route = APIRouter()


@service_route.get('/services', status_code=HTTPStatus.OK, response_model=List[ServiceResponse])
async def get_services(db:DBSession):
    return await user_service.get_services(db)


@service_route.get('/service/{service_id}', status_code=HTTPStatus.OK, response_model=ServiceResponse)
async def get_service(db:DBSession,r:rediscon ,service_id:int):
    return await user_service.get_service(db,r,service_id)
