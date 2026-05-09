from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, delete, exists, func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.models.avaliabilites_models import Avaliabilite
from app.models.psychologist_models import Psychologist
from app.schemas.psychologist_schema import (
    DeleteAvailabilySchema,
    availability_list_adapter,
)


async def get_psych(db: DBSession, id_psych: int) -> Psychologist | None:
    stmt = select(Psychologist).where(Psychologist.user_id == id_psych)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def check_overlapping_availability(
    db: DBSession,
    id_psychologist: int,
    day: int,
    new_start: time,
    new_end: time,
) -> bool:

    stmt = (
        select(Avaliabilite)
        .where(
            and_(
                Avaliabilite.id_psychologist == id_psychologist,
                Avaliabilite.day_of_the_week == day,
                Avaliabilite.start_time < new_end,
                Avaliabilite.end_time > new_start,
            )
        )
        .limit(1)
    )
    result = await db.execute(stmt)

    return result.first() is not None


async def avaliabilite_exists(
    db: DBSession,
    id_psych: int,
    date: datetime,
    service_minutes: int,
) -> bool:
    date_br = date.astimezone(ZoneInfo('America/Sao_Paulo'))

    duration = timedelta(minutes=service_minutes)

    end_time = date_br + duration

    stmt = select(
        exists().where(
            Avaliabilite.id_psychologist == id_psych,
            Avaliabilite.day_of_the_week == date_br.weekday(),
            Avaliabilite.start_time <= date_br.time(),
            Avaliabilite.end_time >= end_time.time(),
        )
    )

    result = await db.execute(stmt)

    return result.scalar()


async def cache_avaliabilites(db: DBSession, r: rediscon, psych_id: int):
    cache_key = f"psychologist:{psych_id}:full_schedule"

    avaliabilite_cache = await r.get(cache_key)

    if avaliabilite_cache:
        return availability_list_adapter.validate_json(avaliabilite_cache)

    stmt = select(Avaliabilite).where(
        Avaliabilite.id_psychologist == psych_id
    ).order_by(Avaliabilite.day_of_the_week)

    result = await db.execute(stmt)
    db_availabilities = result.scalars().all()

    if not db_availabilities:
        return []

    pydantic_availabilities = availability_list_adapter.validate_python(
        db_availabilities
    )

    schedule_json = availability_list_adapter.dump_json(pydantic_availabilities)

    await r.set(
        cache_key,
        schedule_json,
        40400
    )

    return pydantic_availabilities


async def delete_availbilty(
        db: DBSession, user: CurrentUser, day: DeleteAvailabilySchema
) -> dict:
    start_v = day.start_time.replace(second=0, microsecond=0, tzinfo=None)
    end_v = day.end_time.replace(second=0, microsecond=0, tzinfo=None)

    stmt = delete(Avaliabilite).where(
        Avaliabilite.psychologist == user.psychologist_profile,
        Avaliabilite.day_of_the_week == day.days_of_the_week,
        func.date_trunc('minute', Avaliabilite.start_time) == start_v,
        func.date_trunc('minute', Avaliabilite.end_time) == end_v
    )
    try:
        await db.execute(stmt)
        await db.commit()

        return {'message': 'Disponibilidade deletada'}

    except IntegrityError as e:
        await db.rollback()
        raise f"Erro de integridade {e}"
    except OperationalError as e:
        await db.rollback()
        raise f'Erro de operação: {e}'
    except Exception as e:
        await db.rollback()
        raise f'Um erro inesperado ocorreu: {e}'
