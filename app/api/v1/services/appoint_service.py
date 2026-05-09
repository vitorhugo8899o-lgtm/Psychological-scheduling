from typing import List

from fastapi import HTTPException

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.repositories.appointment_repo import (
    check_appointment_conflict,
    create_appointment,
    get_all_psych_appointment,
    get_all_user_appointment,
    search_available_psychologists,
)
from app.api.v1.repositories.psych_repo import avaliabilite_exists, get_psych
from app.api.v1.repositories.service_repo import get_service_by_id
from app.api.v1.util.util import format_hour_br
from app.models.appointments_models import Appointment
from app.schemas.appointment_schema import AppointmentCreate, AppointmentSimulation


async def check_for_conflict(
    db: DBSession, payload: AppointmentCreate, user: CurrentUser
) -> Appointment:

    if user.role != 'cliente':
        raise HTTPException(
            status_code=403,
            detail='É proibido marcar consultas em contas administrativas da clinica, se desejar marcar uma consulta entre com uma conta normal.',  # noqa
        )

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


async def get_user_appointment(db: DBSession, user: CurrentUser) -> List[Appointment]:
    appointments = await get_all_user_appointment(db, user)

    if not appointments:
        raise HTTPException(status_code=404, detail='Nenhuma consulta encontrada.')

    return appointments


async def get_psych_appointment(db: DBSession, user: CurrentUser) -> List[Appointment]:
    if not user.psychologist_profile:
        raise HTTPException(
            status_code=403, detail='Somente psicólogos podem acessar essa função.'
        )

    appointments = await get_all_psych_appointment(db, user)

    if not appointments:
        raise HTTPException(status_code=404, detail='Nenhuma consulta encontrada.')

    return appointments


async def simulation_available_psychologists(
    db: DBSession, simulation: AppointmentSimulation
) -> list:
    service_time = await get_service_by_id(db, simulation.service_id)

    if not service_time:
        raise HTTPException(status_code=404, detail='Serviço não encontrado.')

    search = await search_available_psychologists(
        db, simulation.date_time, service_time.duration_minutes
    )

    if not search:
        date = format_hour_br(simulation.date_time)
        raise HTTPException(
            status_code=404, detail=f'Nehuma disponibilidade para a data: {date}'
        )

    return search
