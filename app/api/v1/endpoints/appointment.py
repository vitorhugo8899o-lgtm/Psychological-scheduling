from http import HTTPStatus

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services.appoint_service import check_for_conflict
from app.schemas.appointment_schema import AppointmentCreate, ApppointmentResponse

appointment_route = APIRouter()


@appointment_route.post(
    '/appointments', status_code=HTTPStatus.CREATED, response_model=ApppointmentResponse
)
async def schedule_an_appointment(
    db: DBSession, user: CurrentUser, payload: AppointmentCreate
):
    return await check_for_conflict(db, payload, user)
