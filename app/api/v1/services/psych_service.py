from fastapi import HTTPException

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.repositories import psych_repo
from app.models.avaliabilites_models import Avaliabilite
from app.schemas.psychologist_schema import PsychologistAvaliabiliteCreate


async def create_avaliabilite(
    db: DBSession,
    r: rediscon,
    user: CurrentUser,
    payload: PsychologistAvaliabiliteCreate,
) -> dict:
    if user.role != 'psychologist':
        raise HTTPException(
            status_code=403,
            detail='O Usuário não tem permissão para realizar essa ação',
        )

    psych = await psych_repo.get_psych(db, user.id)

    if not psych:
        raise HTTPException(
            status_code=409,
            detail='Psicólogo não encontrado! Tente realizar o login novamente',
        )

    availability_to_save = []

    for block in payload.availabilities:
        for day in block.days_of_the_week:
            has_conflict = await psych_repo.check_overlapping_availability(
                db=db,
                id_psychologist=psych.id,
                day=day,
                new_start=block.start_time,
                new_end=block.end_time,
            )

            if has_conflict:
                raise HTTPException(
                    status_code=400,
                    detail=f'Conflito de horário detectado entre {block.start_time.strftime("%H:%M")} e {block.end_time.strftime("%H:%M")}, confira seus horários.',  # noqa
                )

            nova_disponibilidade = Avaliabilite(
                day_of_the_week=day,
                start_time=block.start_time,
                end_time=block.end_time,
                id_psychologist=psych.id,
            )
            availability_to_save.append(nova_disponibilidade)

    db.add_all(availability_to_save)
    await db.commit()

    return {'message': 'Disponibilidades adicionadas com sucesso!'}
