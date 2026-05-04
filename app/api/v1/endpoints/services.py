
from http import HTTPStatus
from typing import List, Annotated
from app.schemas.service_schema import ServiceResponse, ServiceQuery
from app.api.v1.dependencies import DBSession, rediscon, CurrentUser
from fastapi import APIRouter, Query, Depends, Body
from app.api.v1.services import user_service


service_route = APIRouter()


@service_route.get('/services', status_code=HTTPStatus.OK, response_model=List[ServiceResponse])
async def get_services(db:DBSession):
    return await user_service.get_services(db)


@service_route.get('/service/{service_id}', status_code=HTTPStatus.OK, response_model=ServiceResponse)
async def get_service(db:DBSession,r:rediscon ,service_id:int):
    return await user_service.get_service(db,r,service_id)


@service_route.get('/services/filter',status_code=HTTPStatus.OK)
async def fields_services(
    db:DBSession,
    user:CurrentUser,
    filter: ServiceQuery = Depends()
):
    return await user_service.get_service_customized(db,filter)