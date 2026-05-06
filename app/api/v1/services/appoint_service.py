from fastapi import HTTPException

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.repositories.appointment_repo import (
    check_if_psych_has_appointment,
    create_appointment,
)
from app.api.v1.repositories.psych_repo import get_psych
from app.api.v1.repositories.service_repo import get_service_by_id
from app.schemas.appointment_schema import AppointmentCreate


async def check_for_conflict(
    db: DBSession, payload: AppointmentCreate, user: CurrentUser
):

    service = await get_service_by_id(db, payload.service_id)

    if not service:
        raise HTTPException(
            status_code=409,
            detail='Serviço não encontrado, verifique se digitou corretamente.'
        )

    psych = await get_psych(db, payload.id_psychologist)

    if not psych:
        raise HTTPException(
            status_code=409,
            detail=(
                'O Psicólogo não encontrado, verifique se o id digitado é válido'
            ),
        )

    check = await check_if_psych_has_appointment(
        db, payload, psych.id, service.duration_minutes
    )

    if check:
        raise HTTPException(
            status_code=409,
            detail='O psicólogo já possui uma consulta marcada neste horário.',
        )

    appointment = await create_appointment(db, payload, user, psych.id)

    return appointment
