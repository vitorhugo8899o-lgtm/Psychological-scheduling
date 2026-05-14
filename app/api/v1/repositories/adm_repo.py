from sqlalchemy import desc, func, select

from app.api.v1.dependencies import DBSession
from app.models.appointments_models import Appointment
from app.models.paymentes_models import Payment
from app.models.psychologist_models import Psychologist
from app.models.service_models import Service
from app.schemas.service_schema import FinancialSchema, ServiceSchema


async def create_psych(db: DBSession, id_psych: int, crp_psych: str) -> Psychologist:
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


async def total_collected_metrics(db: DBSession, report: FinancialSchema):
    stmt = (
        select(
            Service.name.label("service_name"),
            func.count(Payment.id).label('total_sales')
        )
        .join(Appointment, Payment.id_appointment == Appointment.id)
        .join(Service, Appointment.id_service == Service.id)
        .where(
            Payment.created_at >= report.start_date,
            Payment.created_at < report.end_date
        )
        .group_by(Service.name)
        .order_by(desc('total_sales'))
    )

    result = await db.execute(stmt)

    return [dict(row._mapping) for row in result.all()]
