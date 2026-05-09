from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, exists, select

from app.api.v1.dependencies import DBSession, rediscon
from app.models.avaliabilites_models import Avaliabilite
from app.models.psychologist_models import Psychologist
from app.schemas.psychologist_schema import availability_list_adapter


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
