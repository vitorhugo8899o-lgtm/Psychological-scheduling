import mercadopago
from sqlalchemy import select

from app.api.v1.dependencies import DBSession
from app.core.config import settings
from app.models.appointments_models import Appointment
from app.models.paymentes_models import Payment
from app.schemas.custom_schema import AppointmentStatus
from app.schemas.payment_schema import PaymentDB, PaymentePreference

sdk = mercadopago.SDK(settings.API_KEY_MERCADO_PAGO)


def create_preference(data: PaymentePreference, id_appointment: int):
    preference_data = {
        'items': [
            {
                'title': f'{data.title}',
                'description': f'{data.description}',
                'quantity': 1,
                'unit_price': float(data.unit_price),
                'currency_id': 'BRL',
            }
        ],
        'external_reference': f'Appointment:{id_appointment}',
    }

    preference = sdk.preference().create(preference_data)
    return preference['response']['init_point']


async def get_payment(db: DBSession, data_id: str):
    stmt = select(Payment).where(Payment.id_mercado_pago == data_id)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def create_payment_and_update_appointment(
    db: DBSession, data: PaymentDB, status_appointment: AppointmentStatus
):
    db_payment = Payment(
        id_mercado_pago=data.id_mercado_pago,
        id_appointment=data.id_appointment,
        amount=data.amount,
        status=data.status,
    )

    db.add(db_payment)

    stmt_appointment = select(Appointment).where(Appointment.id == data.id_appointment)
    result_appointment = await db.execute(stmt_appointment)
    db_appointment = result_appointment.scalar_one_or_none()

    if db_appointment:
        db_appointment.status = status_appointment

    await db.commit()
    await db.refresh(db_payment)

    return db_payment
