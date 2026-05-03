from fastapi import HTTPException

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.repositories import adm_repo, user_repo
from app.models.psychologist_models import Psychologist
from app.schemas.custom_schema import UserRole
from app.schemas.psychologist_schema import PsychologistCreate


async def create_psychologist_service(
    db: DBSession, user: CurrentUser,
    psych: PsychologistCreate
) -> Psychologist:
    if user.role != 'adm':
        raise HTTPException(
            status_code=403,
            detail='Usuário não possui permissão para realizar essa ação'
        )

    exists = await user_repo.get_user_by_email(db, psych.email)

    if not exists:
        raise HTTPException(
            status_code=404,
            detail=(
                "Usuário não encontrado,"
                "verifique se digitou corretamente o email"
            )
        )

    if exists.psychologist_profile:
        raise HTTPException(status_code=400, detail="Usuário já é psicólogo")

    exists.role = UserRole.psychologist

    new_psych = await adm_repo.create_psych(db, exists.id, psych.crp_formatado)

    await db.refresh(exists)

    return new_psych
