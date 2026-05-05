from datetime import time

from sqlalchemy import and_, select

from app.api.v1.dependencies import DBSession, rediscon
from app.models.avaliabilites_models import Avaliabilite
from app.models.psychologist_models import Psychologist
from app.schemas.psychologist_schema import availability_list_adapter


async def get_psych(db: DBSession, id_psych: int):
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

    pydantic_availabilities = availability_list_adapter.validate_python(db_availabilities)

    schedule_json = availability_list_adapter.dump_json(pydantic_availabilities)

    await r.set(
        cache_key,
        schedule_json,
        40400
    )

    return pydantic_availabilities
