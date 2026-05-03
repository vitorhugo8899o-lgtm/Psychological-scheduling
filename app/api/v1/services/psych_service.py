from fastapi import HTTPException

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.repositories import psych_repo
from app.schemas.psychologist_schema import PsychologistAvaliabilite


async def create_avaliabilite(
    db: DBSession,
    r: rediscon,
    user: CurrentUser,
    availability: PsychologistAvaliabilite,
):
    if user.role != 'psychologist':
        raise HTTPException(
            status_code=403,
            detail='O Usuário não tem permissão para realzar essa ação',
        )

    psych = await psych_repo.get_psych(db, user.id)

    if not psych:
        raise HTTPException(
            status_code=409,
            detail='Psicólogo não encontrado! Tente realizar o login novamente'
        )

    return await psych_repo.add_availability(db, availability, psych)
