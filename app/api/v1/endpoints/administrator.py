from http import HTTPStatus
from typing import List

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services import adm_service
from app.schemas.psychologist_schema import (
    PsychologistCreate,
    PsychologistPublic,
)
from app.schemas.service_schema import (
    FinancialSchema,
    ServiceMetric,
    ServiceResponse,
    ServiceSchema,
)

adm_router = APIRouter()


@adm_router.post(
    '/psychologist',
    status_code=HTTPStatus.CREATED,
    response_model=PsychologistPublic,
)
async def create_psychologist(
    db: DBSession, user: CurrentUser, psych: PsychologistCreate
):
    return await adm_service.create_psychologist_service(db, user, psych)


@adm_router.post(
    '/services', status_code=HTTPStatus.CREATED, response_model=ServiceResponse
)
async def create_service(db: DBSession, user: CurrentUser, service: ServiceSchema):
    return await adm_service.create_service(db, user.role, service)


@adm_router.post(
    '/financial-report',
    status_code=HTTPStatus.OK,
    response_model=List[ServiceMetric] | dict
)
async def financial_report(db: DBSession, user: CurrentUser, report: FinancialSchema):
    return await adm_service.get_financial_report(db, user, report)
