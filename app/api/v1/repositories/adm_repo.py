from sqlalchemy import select

from app.api.v1.dependencies import DBSession
from app.models.psychologist_models import Psychologist
from app.models.service_models import Service
from app.schemas.service_schema import ServiceSchema


async def create_psych(
    db: DBSession, id_psych: int, crp_psych: str
) -> Psychologist:
    new_psych = Psychologist(user_id=id_psych, crp=crp_psych)

    db.add(new_psych)
    await db.commit()
    await db.refresh(new_psych)

    return new_psych


async def get_service(db: DBSession, name_service: str) -> Service | None:
    stmt = select(Service).where(Service.name == name_service)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def create_service(db: DBSession, service: ServiceSchema) -> Service:
    new_service = Service(
        name=service.name,
        description=service.description,
        price=service.price,
        duration_minutes=service.duration_minutes,
    )

    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)

    return new_service
