from datetime import timedelta

from sqlalchemy import select

from app.api.v1.dependencies import CurrentUser, DBSession
from app.models.appointments_models import Appointment
from app.schemas.appointment_schema import AppointmentCreate
from app.schemas.custom_schema import AppointmentStatus


async def check_if_psych_has_appointment(
    db: DBSession, payload: AppointmentCreate, id_psych: int, time_service: int
):
    duration = timedelta(minutes=time_service)
    start_time = payload.date_time
    end_time = start_time + duration

    stmt = select(Appointment).where(
        Appointment.id_psychologist == id_psych,
        Appointment.status != AppointmentStatus.canceled,
        Appointment.date_time < end_time,
        (Appointment.date_time + duration) > start_time,
    )

    existing_appointment = await db.scalar(stmt)

    return existing_appointment


async def create_appointment(
    db: DBSession, payload: AppointmentCreate, user: CurrentUser, id_psych: int
):
    new_appointment = Appointment(
        id_client=user.id,
        id_psychologist=id_psych,
        id_service=payload.service_id,
        date_time=payload.date_time,
    )

    db.add(new_appointment)
    await db.commit()
    await db.refresh(new_appointment)

    return new_appointment
