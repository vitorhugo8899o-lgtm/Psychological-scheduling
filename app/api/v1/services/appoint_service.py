from fastapi import HTTPException

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.repositories.appointment_repo import (
    check_appointment_conflict,
    create_appointment,
    get_all_psych_appointment,
    get_all_user_appointment,
)
from app.api.v1.repositories.psych_repo import avaliabilite_exists, get_psych
from app.api.v1.repositories.service_repo import get_service_by_id
from app.api.v1.util.util import format_hour_br
from app.schemas.appointment_schema import AppointmentCreate


async def check_for_conflict(
    db: DBSession, payload: AppointmentCreate, user: CurrentUser
):

    service = await get_service_by_id(db, payload.service_id)

    if not service:
        raise HTTPException(
            status_code=409,
            detail='Serviço não encontrado, verifique se digitou corretamente.',
        )

    user_appointment = await check_appointment_conflict(
        db, payload, service.duration_minutes, id_client=user.id
    )

    if user_appointment:
        date = format_hour_br(user_appointment.date_time)
        raise HTTPException(
            status_code=409,
            detail=f'Você já possui uma consulta marcada neste período. Consulta:{date}'
        )

    psych = await get_psych(db, payload.id_psychologist)

    if not psych:
        raise HTTPException(
            status_code=409,
            detail=('O Psicólogo não encontrado, verifique se o id digitado é válido'),
        )

    avaliabilites = await avaliabilite_exists(
        db, psych.id, payload.date_time, service.duration_minutes
    )

    if not avaliabilites:
        raise HTTPException(
            status_code=409,
            detail='O psicólogo solcitado não atende na data informada.',
        )

    psych_appointment = await check_appointment_conflict(
        db, payload, service.duration_minutes, id_psychologist=psych.id
    )

    if psych_appointment:
        date = format_hour_br(psych_appointment.date_time)
        raise HTTPException(
            status_code=409,
            detail=(
                f'O psicólogo já possui uma consulta marcada neste horário. Consulta: {date}'  # noqa
            ),
        )

    appointment = await create_appointment(db, payload, user, psych.id)

    return appointment


async def get_user_appointment(db: DBSession, user: CurrentUser):
    appointments = await get_all_user_appointment(db, user)

    if not appointments:
        raise HTTPException(status_code=404, detail='Nenhuma consulta encontrada.')

    return appointments


async def get_psych_appointment(db: DBSession, user: CurrentUser):
    if not user.psychologist_profile:
        raise HTTPException(
            status_code=403,
            detail="Somente psicólogos podem acessar essa função."
        )

    appointments = await get_all_psych_appointment(db, user)

    if not appointments:
        raise HTTPException(status_code=404, detail='Nenhuma consulta encontrada.')

    return appointments
    