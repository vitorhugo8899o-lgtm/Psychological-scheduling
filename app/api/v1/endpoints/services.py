from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends, Request

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.services import user_service
from app.redis.limiter import limiter
from app.schemas.service_schema import ServiceQuery, ServiceResponse

service_route = APIRouter()


@service_route.get(
    '/services',
    status_code=HTTPStatus.OK,
    response_model=List[ServiceResponse] | str,
)
@limiter.limit('6/minute')
async def get_services(request: Request, db: DBSession, user: CurrentUser):
    return await user_service.get_services(db)


@service_route.get(
    '/service/{service_id}',
    status_code=HTTPStatus.OK,
    response_model=ServiceResponse,
)
@limiter.limit('6/minute')
async def get_service(
    request: Request, db: DBSession, user: CurrentUser, r: rediscon, service_id: int
):
    return await user_service.get_service(db, r, service_id)


@service_route.get('/services/filter', status_code=HTTPStatus.OK)
@limiter.limit('5/minute')
async def fields_services(
    request: Request,
    db: DBSession,
    user: CurrentUser,
    filter: Annotated[ServiceQuery, Depends()],
):
    return await user_service.get_service_customized(db, filter)
