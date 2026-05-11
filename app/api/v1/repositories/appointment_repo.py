from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import and_, case, delete, exists, not_, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import joinedload

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.util.util import ensure_utc
from app.models.appointments_models import Appointment
from app.models.avaliabilites_models import Avaliabilite
from app.models.psychologist_models import Psychologist
from app.models.users_models import User
from app.schemas.appointment_schema import AppointmentCreate
from app.schemas.custom_schema import AppointmentStatus


async def check_appointment_conflict(
    db: DBSession,
    payload: AppointmentCreate,
    time_service: int,
    *,
    id_psychologist: int | None = None,
    id_client: int | None = None,
) -> Appointment | None:
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
) -> Appointment:
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


async def get_all_user_appointment(
    db: DBSession, user: CurrentUser
) -> List[Appointment] | None:
    stmt = (
        select(Appointment)
        .where(
            Appointment.id_client == user.id,
        )
        .order_by(
            case(
                (Appointment.status == AppointmentStatus.pending, 0),
                (Appointment.status == AppointmentStatus.confirmed, 1),
                else_=2,
            )
        )
    )

    result = await db.execute(stmt)

    return result.scalars().all()


async def get_all_psych_appointment(
    db: DBSession, user: CurrentUser
) -> List[Appointment] | None:
    stmt = (
        select(Appointment)
        .where(
            Appointment.psychologist == user.psychologist_profile,
        )
        .order_by(
            case(
                (Appointment.status == AppointmentStatus.pending, 0),
                (Appointment.status == AppointmentStatus.confirmed, 1),
                else_=2,
            )
        )
    )

    result = await db.execute(stmt)

    return result.scalars().all()


async def delete_appointment_user(db: DBSession, user: CurrentUser):
    stmt = delete(Appointment).where(Appointment.id_client == user.id)

    try:
        await db.execute(stmt)

        await db.commit()
    except OperationalError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f'{e}')
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f'{e}')


async def search_available_psychologists(
    db: DBSession, search_date: datetime, service_time: int
) -> list:

    tz_br = ZoneInfo('America/Sao_Paulo')

    date_br = search_date.astimezone(tz_br)

    day_of_week = date_br.weekday()
    start_time_br = date_br.time()

    duration = timedelta(minutes=service_time)
    end_time = (date_br + duration).time()

    stmt = (
        select(Psychologist, User.fullname)
        .distinct()
        .join(User, Psychologist.user_id == User.id)
        .join(Avaliabilite, Avaliabilite.id_psychologist == Psychologist.id)
        .where(
            and_(
                Avaliabilite.day_of_the_week == day_of_week,
                Avaliabilite.start_time <= start_time_br,
                Avaliabilite.end_time >= end_time,
            )
        )
    ).where(
        not_(
            exists().where(
                and_(
                    Appointment.id_psychologist == Psychologist.id,
                    Appointment.status != AppointmentStatus.canceled,
                    Appointment.date_time < (search_date + duration),
                )
            )
        )
    )

    result = await db.execute(stmt)

    available_data = []
    for psych, fullname in result.all():
        available_data.append({'id': psych.id, 'fullname': fullname, 'crp': psych.crp})

    return available_data


async def get_appointment_by_id(db: DBSession, appoinment_id: int, user_id: id):
    stmt = (
        select(Appointment)
        .options(joinedload(Appointment.service))
        .where(Appointment.id == appoinment_id, Appointment.id_client == user_id)
    )

    result = await db.execute(stmt)

    return result.scalar_one_or_none()
