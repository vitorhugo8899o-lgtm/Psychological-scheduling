from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Request

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services.appoint_service import (
    cancel_service,
    check_for_conflict,
    rescheduling_appointmnet,
    simulation_available_psychologists,
)
from app.redis.limiter import limiter
from app.schemas.appointment_schema import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentSimulation,
    CancelAppointment,
    PsychSearchResponse,
    ReschedulingAppointment,
)

appointment_route = APIRouter()


@appointment_route.post(
    '/appointments', status_code=HTTPStatus.CREATED, response_model=AppointmentResponse
)
async def schedule_an_appointment(
    request: Request, db: DBSession, user: CurrentUser, payload: AppointmentCreate
):
    return await check_for_conflict(db, payload, user)


@appointment_route.post(
    '/appointments/simulation',
    status_code=HTTPStatus.OK,
    response_model=List[PsychSearchResponse],
)
@limiter.limit('3/minute')
async def get_simulation_appointment(
    request: Request,
    db: DBSession,
    user: CurrentUser,
    simulation: AppointmentSimulation,
):
    return await simulation_available_psychologists(db, simulation)


@appointment_route.post(
    '/appointments/rescheduling',
    status_code=HTTPStatus.OK,
    response_model=AppointmentResponse,
)
@limiter.limit('3/hour')
async def rescheduling(
    request: Request,
    user: CurrentUser,
    db: DBSession,
    appointment: ReschedulingAppointment,
):
    return await rescheduling_appointmnet(db, user, appointment)


@appointment_route.post(
    '/appointments/cancel',
    status_code=HTTPStatus.OK,
    response_model=AppointmentResponse,
)
@limiter.limit('3/minute')
async def cancel_appointment(
    request: Request, db: DBSession, user: CurrentUser, appointmnet: CancelAppointment
):
    return await cancel_service(db, user, appointmnet.id_appointment)
