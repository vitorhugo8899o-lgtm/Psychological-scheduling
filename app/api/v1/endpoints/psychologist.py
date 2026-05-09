from http import HTTPStatus
from typing import List

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.services import appoint_service, psych_service
from app.schemas.appointment_schema import AppointmentUserResponse
from app.schemas.psychologist_schema import PsychologistAvaliabiliteCreate

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
