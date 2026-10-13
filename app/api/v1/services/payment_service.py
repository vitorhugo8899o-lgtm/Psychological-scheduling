import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import sentry_sdk
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.v1.dependencies import DBSession
from app.api.v1.repositories import appointment_repo, payment_repo
from app.api.v1.repositories.payment_repo import get_payment, sdk
from app.api.v1.util.util import ensure_utc, pending_expired
from app.core.config import settings
from app.models.appointments_models import Appointment
from app.models.paymentes_models import Payment
from app.schemas.custom_schema import AppointmentStatus, PaymentStatus
from app.schemas.payment_schema import PaymentCreate, PaymentePreference

CURRENCY = 'BRL'
MP_REJECTED = {'rejected', 'cancelled'}
MP_REVERSED = {'refunded', 'charged_back'}


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

    # Só se paga uma consulta que está aguardando pagamento e ainda vai acontecer:
    # evita pagar duas vezes, pagar consulta cancelada (e "ressuscitá-la" depois)
    # e abrir checkout de consulta que já passou.
    if result.status != AppointmentStatus.pending:
        raise HTTPException(
            status_code=409, detail='Esta consulta não está aguardando pagamento.'
        )

    if ensure_utc(result.date_time) <= datetime.now(UTC):
        raise HTTPException(
            status_code=409, detail='Esta consulta já passou. Faça um novo agendamento.'
        )

    if pending_expired(result.created_at, settings.PENDING_APPOINTMENT_TTL_MINUTES):
        raise HTTPException(
            status_code=409,
            detail=(
                'O prazo para pagamento desta consulta expirou. '
                'Faça um novo agendamento.'
            ),
        )

    data = PaymentePreference(
        title=result.service.name,
        description=result.service.description,
        unit_price=result.service.price,
    )

    # O SDK do Mercado Pago é síncrono: roda em thread para não travar a API toda.
    checkout_url = await asyncio.to_thread(
        payment_repo.create_preference, data, appointment.appointment_id
    )

    return {'checkout_url': checkout_url}


def _flag_for_review(appointment_id: int, mp_payment_id: str, reason: str) -> None:
    """Dinheiro recebido que NÃO confirmou a consulta: precisa de ação manual."""
    message = (
        f'[Pagamento] Revisão manual/reembolso: {reason} '
        f'(consulta={appointment_id}, pagamento_mp={mp_payment_id})'
    )
    logging.warning(message)
    sentry_sdk.capture_message(message, level='warning')


def _to_decimal(value) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


async def _apply_approved(
    db: DBSession, appointment: Appointment, amount_ok: bool, mp_payment_id: str
) -> None:
    if appointment.status == AppointmentStatus.pending:
        if not amount_ok:
            _flag_for_review(
                appointment.id, mp_payment_id, 'valor/moeda diferente do serviço'
            )
        elif await appointment_repo.find_confirmed_overlap(db, appointment):
            _flag_for_review(
                appointment.id,
                mp_payment_id,
                'horário já ocupado por outra consulta confirmada',
            )
        else:
            appointment.status = AppointmentStatus.confirmed

    elif appointment.status == AppointmentStatus.canceled:
        # Nunca reativa consulta cancelada: o horário pode já ter sido reservado.
        _flag_for_review(
            appointment.id, mp_payment_id, 'pagamento aprovado de consulta cancelada'
        )


HTTP_OK = 200
IGNORED = {'success': True, 'detail': 'Evento ignorado'}


async def _fetch_mp_payment(data_id) -> dict:
    # Chamada síncrona do SDK -> thread (não bloqueia o event loop).
    payment_response = await asyncio.to_thread(lambda: sdk.payment().get(data_id))
    payment = payment_response.get('response')

    if payment_response.get('status', HTTP_OK) != HTTP_OK or not payment:
        raise HTTPException(
            status_code=400, detail='Pagamento não encontrado no Mercado Pago'
        )

    return payment


def _appointment_id_from(payment: dict) -> int | None:
    reference = payment.get('external_reference') or ''

    if not reference.startswith('Appointment:'):
        return None

    try:
        return int(reference.split(':')[1])
    except (IndexError, ValueError):
        return None


def _map_status(mp_status: str | None) -> PaymentStatus:
    if mp_status == 'approved':
        return PaymentStatus.approved

    if mp_status in MP_REJECTED or mp_status in MP_REVERSED:
        return PaymentStatus.rejected

    return PaymentStatus.pending


def _check_amount(payment: dict, appointment: Appointment) -> tuple[Decimal, bool]:
    amount = _to_decimal(payment.get('transaction_amount', 0)) or Decimal(0)
    expected = _to_decimal(appointment.service.price)

    amount_ok = (
        expected is not None
        and amount == expected
        and payment.get('currency_id', CURRENCY) == CURRENCY
    )

    return amount, amount_ok


async def _apply_transition(
    db: DBSession,
    appointment: Appointment,
    mp_status: str | None,
    amount_ok: bool,
    mp_payment_id: str,
) -> None:
    """Máquina de estados da consulta.

    - aprovado  -> confirma SOMENTE se pendente, valor correto e horário livre;
    - recusado  -> só registra o pagamento (o cliente pode tentar de novo no mesmo
                   checkout; a consulta pendente expira sozinha);
    - estornado -> cancela a consulta que estava confirmada.
    """
    if _map_status(mp_status) == PaymentStatus.approved:
        await _apply_approved(db, appointment, amount_ok, mp_payment_id)
    elif mp_status in MP_REVERSED and appointment.status == AppointmentStatus.confirmed:
        appointment.status = AppointmentStatus.canceled
        _flag_for_review(appointment.id, mp_payment_id, f'pagamento {mp_status}')


async def _commit_payment(
    db: DBSession, db_payment: Payment, mp_payment_id: str
) -> Payment:
    try:
        await db.commit()
    except IntegrityError:
        # Entrega concorrente do mesmo webhook já gravou o pagamento.
        await db.rollback()
        existing = await get_payment(db, mp_payment_id)
        if existing:
            return existing
        raise

    await db.refresh(db_payment)

    return db_payment


async def process_update_payment(db: DBSession, data_id, event_type):
    if not data_id or event_type != 'payment':
        return IGNORED

    payment = await _fetch_mp_payment(data_id)
    appointment_id = _appointment_id_from(payment)

    if appointment_id is None:
        return {'success': True, 'detail': 'Não é um pagamento de consulta'}

    mp_payment_id = str(data_id)

    # Trava a consulta: dois webhooks do mesmo pagamento/consulta não correm juntos.
    appointment = await appointment_repo.get_appointment_for_update(db, appointment_id)

    if not appointment:
        _flag_for_review(appointment_id, mp_payment_id, 'consulta inexistente')
        return {'success': True, 'detail': 'Consulta não encontrada'}

    db_payment = await get_payment(db, mp_payment_id)

    if db_payment and db_payment.id_appointment != appointment.id:
        # Um mesmo pagamento nunca muda de consulta.
        _flag_for_review(
            appointment.id, mp_payment_id, 'pagamento já vinculado a outra consulta'
        )
        return {'success': True, 'detail': 'Pagamento já vinculado a outra consulta'}

    mp_status = payment.get('status')
    new_status = _map_status(mp_status)
    amount, amount_ok = _check_amount(payment, appointment)

    await _apply_transition(db, appointment, mp_status, amount_ok, mp_payment_id)

    if db_payment:
        db_payment.status = new_status
    else:
        db_payment = Payment(
            id_mercado_pago=mp_payment_id,
            id_appointment=appointment.id,
            amount=amount,
            status=new_status,
        )
        db.add(db_payment)

    return await _commit_payment(db, db_payment, mp_payment_id)
