from datetime import timedelta

from sqlalchemy import case, select

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.util.util import ensure_utc
from app.models.appointments_models import Appointment
from app.schemas.appointment_schema import AppointmentCreate
from app.schemas.custom_schema import AppointmentStatus


async def check_appointment_conflict(
    db: DBSession,
    payload: AppointmentCreate,
    time_service: int,
    *,
    id_psychologist: int | None = None,
    id_client: int | None = None,
):
    new_start = ensure_utc(payload.date_time)
    new_end = new_start + timedelta(minutes=time_service)

    stmt = select(Appointment).where(
        Appointment.status != AppointmentStatus.canceled,
    )

    if id_psychologist:
        stmt = stmt.where(Appointment.id_psychologist == id_psychologist)

    if id_client:
        stmt = stmt.where(Appointment.id_client == id_client)

    result = await db.scalars(stmt)

    appointments = result.all()

    for appointment in appointments:
        service = appointment.service

        existing_start = ensure_utc(appointment.date_time)

        existing_end = existing_start + timedelta(minutes=service.duration_minutes)

        has_conflict = existing_start < new_end and existing_end > new_start

        if has_conflict:
            return appointment

    return None


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


async def get_all_user_appointment(db: DBSession, user: CurrentUser):
    stmt = select(Appointment).where(
        Appointment.id_client == user.id,
    ).order_by(
        case(
            (Appointment.status == AppointmentStatus.pending, 0),
            (Appointment.status == AppointmentStatus.confirmed, 1),
            else_=2
        )
    )

    result = await db.execute(stmt)

    return result.scalars().all()


async def get_all_psych_appointment(db: DBSession, user: CurrentUser):
    stmt = select(Appointment).where(
        Appointment.psychologist == user.psychologist_profile,
    ).order_by(
        case(
            (Appointment.status == AppointmentStatus.pending, 0),
            (Appointment.status == AppointmentStatus.confirmed, 1),
            else_=2
        )
    )

    result = await db.execute(stmt)

    return result.scalars().all()
