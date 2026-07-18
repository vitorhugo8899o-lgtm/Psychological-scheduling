from fastapi import HTTPException

from app.api.v1.dependencies import DBSession
from app.api.v1.repositories import appointment_repo, payment_repo
from app.api.v1.repositories.payment_repo import (
    create_payment_and_update_appointment,
    get_payment,
    sdk,
)
from app.schemas.custom_schema import AppointmentStatus, PaymentStatus
from app.schemas.payment_schema import PaymentCreate, PaymentDB, PaymentePreference


async def prepare_data_for_payment(
    db: DBSession, appointment: PaymentCreate, user_id: int
) -> dict:
    result = await appointment_repo.get_appointment_by_id(
        db, appointment.appointment_id, user_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail='Erro ao tentar encontrar a consulta, tente novamente.',
        )

    data = PaymentePreference(
        title=result.service.name,
        description=result.service.description,
        unit_price=result.service.price,
    )

    process_data = payment_repo.create_preference(data, appointment.appointment_id)

    return {'checkout_url': process_data}


async def process_update_payment(db: DBSession, data_id, event_type):
    if not data_id or event_type != 'payment':
        return {'success': True, 'detail': 'Evento ignorado'}

    payment_response = sdk.payment().get(data_id)
    payment = payment_response.get('response')

    if not payment:
        raise HTTPException(
            status_code=400, detail='Pagamento não encontrado no Mercado Pago'
        )

    status = payment.get('status')
    external_reference = payment.get('external_reference')
    transaction_amount = payment.get('transaction_amount', 0.0)

    try:
        if not external_reference or not external_reference.startswith('Appointment:'):
            return {'success': True, 'detail': 'Não é um pagamento de consulta'}
        appointment_id = int(external_reference.split(':')[1])
    except IndexError, ValueError:
        return {'success': True, 'detail': 'Formato de external_reference inválido'}

    if status == 'approved':
        new_payment_status = PaymentStatus.approved
        new_appointment_status = AppointmentStatus.confirmed

    elif status in {'rejected', 'cancelled'}:
        new_payment_status = PaymentStatus.rejected
        new_appointment_status = AppointmentStatus.canceled

    else:
        new_payment_status = PaymentStatus.pending
        new_appointment_status = AppointmentStatus.pending

    db_payment = await get_payment(db, str(data_id))

    if db_payment:
        db_payment.status = new_payment_status
    else:
        data_payment = PaymentDB(
            id_mercado_pago=str(data_id),
            id_appointment=appointment_id,
            amount=transaction_amount,
            status=new_payment_status,
        )
        result = await create_payment_and_update_appointment(
            db, data_payment, new_appointment_status
        )

    return result
