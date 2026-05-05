from http import HTTPStatus
from typing import List

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.services import psych_service
from app.schemas.psychologist_schema import (
    AvailabilityCacheSchema,
    PsychologistAvaliabiliteCreate,
)

psych_router = APIRouter()


@psych_router.post(
    '/psych/me/availability',
    status_code=HTTPStatus.CREATED,
)
async def create_appointment(
    db: DBSession,
    r: rediscon,
    user: CurrentUser,
    availability: PsychologistAvaliabiliteCreate,
):
    return await psych_service.create_avaliabilite(db, r, user, availability)


@psych_router.get(
    '/psych/me/availability',
    status_code=HTTPStatus.OK,
    response_model=List[AvailabilityCacheSchema]
)
async def get_schedule(db: DBSession, r: rediscon, user: CurrentUser):
    return await psych_service.get_avaliabilites(db, r, user)
