from http import HTTPStatus
from typing import List

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services.appoint_service import (
    check_for_conflict,
    rescheduling_appointmnet,
    simulation_available_psychologists,
)
from app.schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentSimulation,
    PsychSearchResponse,
    ReschedulingAppointment,
)

appointment_route = APIRouter()


@appointment_route.post(
    '/appointments', status_code=HTTPStatus.CREATED, response_model=AppointmentResponse
)
async def schedule_an_appointment(
    db: DBSession, user: CurrentUser, payload: AppointmentCreate
):
    return await check_for_conflict(db, payload, user)


@appointment_route.post(
    '/appointments/simulation',
    status_code=HTTPStatus.OK,
    response_model=List[PsychSearchResponse],
)
async def get_simulation_appointment(
    db: DBSession, user: CurrentUser, simulation: AppointmentSimulation
):
    return await simulation_available_psychologists(db, simulation)


@appointment_route.post(
    '/appointments/rescheduling',
    status_code=HTTPStatus.OK,
    response_model=AppointmentResponse,
)
async def rescheduling(
    user: CurrentUser, db: DBSession, appointment: ReschedulingAppointment
):
    return await rescheduling_appointmnet(db, user, appointment)
