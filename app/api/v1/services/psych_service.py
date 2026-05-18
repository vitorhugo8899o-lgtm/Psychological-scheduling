from fastapi import HTTPException

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.repositories import psych_repo, user_repo
from app.api.v1.util.util import cauculation_rate
from app.models.avaliabilites_models import Avaliabilite
from app.schemas.psychologist_schema import (
    DeleteAvailabilySchema,
    MedicalRecordCreate,
    MedicalResponseAll,
    PsychologistAvaliabiliteCreate,
    ResponseRate,
    SchemaMetrics,
)


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


async def get_avaliabilites(db: DBSession, r: rediscon, psych: CurrentUser):
    if not psych.psychologist_profile:
        raise HTTPException(
            status_code=403,
            detail='O Usuário não tem permissão para realizar essa ação.',
        )

    psych_id = await psych_repo.get_psych(db, psych.id)

    schedule = await psych_repo.cache_avaliabilites(db, r, psych_id.id)

    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f'Nenhum horário encontrado.:{schedule} and {psych.id}',
        )

    return schedule


async def delete_availbility_psych(
    db: DBSession, user: CurrentUser, availabily: DeleteAvailabilySchema
):
    if not user.psychologist_profile:
        raise HTTPException(
            status_code=403,
            detail='Usuário não tem permissão para realizar essa função',
        )

    result = await psych_repo.delete_availbilty(db, user, availabily)

    if not result:
        raise HTTPException(
            status_code=404, detail='Nenhuma disponibilidade encontrada.'
        )

    return result


async def get_appoinment_count(db: DBSession, user: CurrentUser, date: SchemaMetrics):
    if not user.psychologist_profile:
        raise HTTPException(
            status_code=403,
            detail='O usuário não tem permissõa para realizar essa ação.',
        )

    metrics = await psych_repo.get_count_appoinment(db, user, date)

    if not metrics:
        return {
            'total': 0,
            'message': f'Nenhum dado encontrado no período de {date.start_date} a {date.end_date}',  # noqa
        }

    return {
        'total': f'{metrics}',
        'message': f'Total de consultas realizadas entre {date.start_date} a {date.end_date}',  # noqa
    }


async def get_rate(db: DBSession, user: CurrentUser):
    if not user.psychologist_profile:
        raise HTTPException(
            status_code=403,
            detail='O usuário não tem permissõa para realizar essa ação.',
        )

    metrics = await psych_repo.get_appoiment_rate(db, user)

    if metrics.total_appoinments == 0:
        return {'message': 'Você não possui nenhum dado de consulta.'}

    cancelation_rate = cauculation_rate(
        metrics.total_appoinments, metrics.total_cancelled
    )

    confirmed_rate = cauculation_rate(
        metrics.total_appoinments, metrics.total_confirmed
    )

    return ResponseRate(
        total_appoinments=metrics.total_appoinments,
        total_cancelled=metrics.total_cancelled,
        total_confirmed=metrics.total_confirmed,
        cancelation_rate=f'{cancelation_rate}%',
        confirmed_rate=f'{confirmed_rate}%',
    )


async def get_psych(db: DBSession):
    psychs = await psych_repo.get_all_psych(db)

    if not psychs:
        raise HTTPException(status_code=404, detail='Nenhum psicólogo encontrado.')

    return psychs


async def medical_record(db: DBSession, user: CurrentUser, record: MedicalRecordCreate):
    if user.role != 'psychologist':
        raise HTTPException(
            status_code=403,
            detail='O usuário não tem permissão para realizar essa ação.',
        )

    exists_user = await user_repo.get_user_by_id(db, record.id_user)

    if not exists_user:
        raise HTTPException(
            status_code=404,
            detail='O usuário não encontrado, verifique se o id digitado está correto.',
        )

    consulted = await psych_repo.consulted_user(db, user, record)

    if not consulted:
        raise HTTPException(
            status_code=409, detail='Você ainda não teve uma consulta com esse usuário.'
        )

    return await psych_repo.create_medical_record(
        db, user, record, consulted.id_service
    )


async def get_records(db: DBSession, user: CurrentUser):
    if user.role != 'psychologist':
        raise HTTPException(
            status_code=403,
            detail='O usuário não tem permissão para realizar essa ação.',
        )

    list_records = []

    medical_records = await psych_repo.get_medical_records(db, user)

    if not medical_records:
        return {'message': 'Nenhum Prontuário registrado.'}

    for record in medical_records:
        entry = MedicalResponseAll(
            id=record.id,
            id_psychologist=user.psychologist_profile.id,
            id_client=record.id_client,
            id_service=record.id_service,
            description=record.description,
            service_name=record.service.name,
            psych_fullname=user.fullname,
            client_name=record.client.fullname,
            created_at=record.created_at,
        )
        list_records.append(entry)

    return list_records


async def get_user_records(db: DBSession, user: CurrentUser, user_id: int):
    if user.role != 'psychologist':
        raise HTTPException(
            status_code=403,
            detail='O usuário não tem permissão para realizar essa ação.',
        )

    list_records = []

    medical_records = await psych_repo.ger_medical_records_by_user(db, user, user_id)

    if not medical_records:
        return {'message': 'Nenhum Prontuário registrado.'}

    for record in medical_records:
        entry = MedicalResponseAll(
            id=record.id,
            id_psychologist=user.psychologist_profile.id,
            id_client=record.id_client,
            id_service=record.id_service,
            description=record.description,
            service_name=record.service.name,
            psych_fullname=user.fullname,
            client_name=record.client.fullname,
            created_at=record.created_at,
        )
        list_records.append(entry)

    return list_records


async def delete_medical_redord(db: DBSession, user: CurrentUser, record_id: int):
    if user.role != 'psychologist':
        raise HTTPException(
            status_code=403,
            detail='O usuário não tem permissão para realizar essa ação.',
        )

    result = await psych_repo.delete_record(db, user, record_id)

    if not result:
        raise HTTPException(status_code=404, detail='Prontuário não encontrado.')
