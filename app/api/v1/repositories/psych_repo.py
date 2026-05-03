
from sqlalchemy import select

from app.api.v1.dependencies import DBSession
from app.models.avaliabilites_models import Avaliabilite
from app.models.psychologist_models import Psychologist
from app.schemas.psychologist_schema import PsychologistAvaliabilite


async def get_psych(db: DBSession, id_psych: int):
    stmt = select(Psychologist).where(Psychologist.user_id == id_psych)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def add_availability(
    db: DBSession,
    availability: PsychologistAvaliabilite,
    psych: Psychologist
):

    disposition = Avaliabilite(
        day_of_the_week=availability.day_of_the_week,
        start_time=availability.start_time,
        end_time=availability.end_time,
        psychologist=psych
    )

    db.add(disposition)
    await db.commit()
    await db.refresh(disposition)

    return disposition
