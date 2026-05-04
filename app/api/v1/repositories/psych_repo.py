from sqlalchemy import select, and_
from datetime import time

from app.api.v1.dependencies import DBSession
from app.models.avaliabilites_models import Avaliabilite
from app.models.psychologist_models import Psychologist


async def get_psych(db: DBSession, id_psych: int):
    stmt = select(Psychologist).where(Psychologist.user_id == id_psych)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def check_overlapping_availability(
    db: DBSession, 
    id_psychologist: int, 
    day: int, 
    new_start: time, 
    new_end: time
) -> bool:
    
    stmt = select(Avaliabilite).where(
        and_(
            Avaliabilite.id_psychologist == id_psychologist,
            Avaliabilite.day_of_the_week == day,
            Avaliabilite.start_time < new_end,
            Avaliabilite.end_time > new_start
        )
    ).limit(1)
    result = await db.execute(stmt)

    return result.first() is not None

