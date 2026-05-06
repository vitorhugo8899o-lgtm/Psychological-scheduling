from fastapi import HTTPException
from datetime import datetime

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.repositories.appointment_repo import (
    check_if_psych_has_appointment,
    create_appointment,
)
from app.api.v1.repositories.psych_repo import get_psych, avaliabilite_exists
from app.api.v1.repositories.service_repo import get_service_by_id
from app.api.v1.repositories.user_repo import check_conflit_appointment_user
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
    
    user_appointment = await check_conflit_appointment_user(
        db,user.id,payload,service.duration_minutes
    )

    if user_appointment:
        raise HTTPException(
            status_code=409,
            detail=f"Você já possui uma consulta marcada ás {user_appointment.date_time}"
        )

    psych = await get_psych(db, payload.id_psychologist)

    if not psych:
        raise HTTPException(
            status_code=409,
            detail=(
                'O Psicólogo não encontrado, verifique se o id digitado é válido'
            ),
        )
    
    avaliabilites = await avaliabilite_exists(db,psych.id,payload.date_time)

    if not avaliabilites:
        raise HTTPException(
            status_code=409,
            detail=f"O psicólogo não atende no dia solcitado."
        )


    check = await check_if_psych_has_appointment(
        db, payload, psych.id, service.duration_minutes
    )

    if check:
        raise HTTPException(
            status_code=409,
            detail=f'O psicólogo já possui uma consulta marcada neste horário.',
        )

    appointment = await create_appointment(db, payload, user, psych.id)

    return appointment
