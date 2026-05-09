from http import HTTPStatus
from typing import List

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.services import appoint_service, psych_service
from app.schemas.appointment_schema import AppointmentUserResponse
from app.schemas.psychologist_schema import (
    AvailabilityCacheSchema,
    DeleteAvailabilySchema,
    PsychologistAvaliabiliteCreate,
)

psych_router = APIRouter()


@psych_router.post(
    '/psych/me/availability',
    status_code=HTTPStatus.CREATED,
)
async def create_avaliabilite(
    db: DBSession,
    r: rediscon,
    user: CurrentUser,
    availability: PsychologistAvaliabiliteCreate,
):
    return await psych_service.create_avaliabilite(db, r, user, availability)


@psych_router.get(
    '/psych/me/appointments',
    status_code=HTTPStatus.OK,
    response_model=List[AppointmentUserResponse],
)
async def get_appiontment(db: DBSession, user: CurrentUser):
    return await appoint_service.get_psych_appointment(db, user)


@psych_router.get(
    '/psych/me/availability',
    status_code=HTTPStatus.OK,
    response_model=List[AvailabilityCacheSchema]
)
async def get_schedule(db: DBSession, r: rediscon, user: CurrentUser):
    return await psych_service.get_avaliabilites(db, r, user)


@psych_router.delete(
    '//psych/me/availability',
    status_code=HTTPStatus.OK,
    response_model=dict
)
async def delete_availbily(
    db: DBSession, user: CurrentUser, availability: DeleteAvailabilySchema
):
    return await psych_service.delete_availbility_psych(db, user, availability)
