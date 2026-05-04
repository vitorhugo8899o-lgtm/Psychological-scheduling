from sqlalchemy import select

from app.api.v1.dependencies import DBSession, rediscon
from app.models.service_models import Service
from app.schemas.service_schema import ServiceQuery, ServiceResponse


async def get_services(db: DBSession):
    stmt = select(Service).limit(100).order_by(Service.id)

    result = await db.execute(stmt)

    return result.scalars().all()


async def get_service_by_id(db: DBSession, service_id: int):
    stmt = select(Service).where(Service.id == service_id)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def cache_service(db: DBSession, r: rediscon, service_id: int):
    cache_key = f'service{service_id}'
    service_cache = await r.get(cache_key)

    if service_cache:
        return ServiceResponse.model_validate_json(service_cache)

    service_obj = await get_service_by_id(db, service_id)

    if service_obj:
        service_schema = ServiceResponse.model_validate(service_obj)

        await r.set(cache_key, service_schema.model_dump_json(), ex=600)

        return service_schema

    return None


async def filter_services(db: DBSession, filter_query: ServiceQuery):
    q = select(Service)

    filter_data = filter_query.model_dump(
        exclude={'limit', 'offset'}, exclude_none=True
    )

    for field, value in filter_data.items():
        if field == 'name':
            q = q.filter(Service.name.ilike(f'%{value}%'))

        elif hasattr(Service, field):
            db_attribute = getattr(Service, field)
            q = q.filter(db_attribute == value)

    if filter_query.limit > 0:
        q = q.limit(filter_query.limit)

    q = q.offset(filter_query.offset)

    result = await db.scalars(q)
    return result.all()
