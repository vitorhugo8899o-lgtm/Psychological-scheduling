import logging

import mercadopago
from fastapi import HTTPException
from sqlalchemy import select

from app.api.v1.dependencies import DBSession
from app.core.config import settings
from app.models.paymentes_models import Payment
from app.schemas.payment_schema import PaymentePreference

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
        'back_urls': {
            'success': f'{settings.LINK_FRONTEND}payment-confirm',
            'failure': f'{settings.LINK_FRONTEND}',
            'pending': f'{settings.LINK_FRONTEND}',
        },
        'auto_return': 'approved',
        'external_reference': f'Appointment:{id_appointment}',
        'notification_url': 'https://psychological-scheduling.onrender.com/api/v1/payments/webhook',
    }

    # Função SÍNCRONA (SDK usa requests): chame com asyncio.to_thread a partir de
    # código async para não bloquear o event loop.
    preference = sdk.preference().create(preference_data)

    init_point = (preference.get('response') or {}).get('init_point')
    http_status = preference.get('status')

    if (http_status is not None and http_status not in {200, 201}) or not init_point:
        logging.error(
            '[Pagamento] Mercado Pago recusou a criação da preferência: status=%s',
            http_status,
        )
        raise HTTPException(
            status_code=502,
            detail='Não foi possível iniciar o pagamento agora. Tente novamente.',
        )

    return init_point


async def get_payment(db: DBSession, data_id: str):
    stmt = select(Payment).where(Payment.id_mercado_pago == data_id)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()
