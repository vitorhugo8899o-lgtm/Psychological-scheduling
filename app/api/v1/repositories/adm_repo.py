from app.api.v1.dependencies import DBSession
from app.models.psychologist_models import Psychologist


async def create_psych(
    db: DBSession, id_psych: int, crp_psych: str
) -> Psychologist:
    new_psych = Psychologist(user_id=id_psych, crp=crp_psych)

    db.add(new_psych)
    await db.commit()
    await db.refresh(new_psych)

    return new_psych
