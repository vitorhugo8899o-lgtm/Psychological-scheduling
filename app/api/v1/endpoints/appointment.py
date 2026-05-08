from typing import List

from http import HTTPStatus

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services.appoint_service import check_for_conflict, simulation_available_psychologists
from app.schemas.appointment_schema import AppointmentCreate, AppointmentResponse, AppointmentSimulation, PsychSearchResponse

appointment_route = APIRouter()


@appointment_route.post(
    '/appointments', status_code=HTTPStatus.CREATED, response_model=AppointmentResponse
)
async def schedule_an_appointment(
    db: DBSession, user: CurrentUser, payload: AppointmentCreate
):
    return await check_for_conflict(db, payload, user)


@appointment_route.post('/appointments/simulation', status_code=HTTPStatus.OK, response_model=List[PsychSearchResponse])
async def get_simulation_appointment(
    db:DBSession,
    user: CurrentUser,
    simulation: AppointmentSimulation
):
    return await simulation_available_psychologists(db,simulation)
