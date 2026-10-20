"""Testes de regressão do fluxo de pagamento (auditoria de segurança)."""

import asyncio
import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app import models
from app.core.config import settings
from app.schemas.custom_schema import AppointmentStatus, PaymentStatus
from tests.conftest import TestingSessionLocal

WEBHOOK = '/api/v1/payments/webhook'
VALIDATOR = 'app.api.v1.endpoints.payment.WebhookSignatureValidator.validate'
MP_SDK_PAYMENT = 'app.api.v1.repositories.payment_repo.sdk.payment'
MP_SDK_PREFERENCE = 'app.api.v1.repositories.payment_repo.sdk.preference'
FLAG = 'app.api.v1.services.payment_service._flag_for_review'
APPOINTMENT_AT = datetime(2026, 5, 11, 14, 30, tzinfo=timezone.utc)
SERVICE_PRICE = 90
PENDING = AppointmentStatus.pending
CONFIRMED = AppointmentStatus.confirmed
CANCELED = AppointmentStatus.canceled


class Scenario:
    """Cliente logado + psicólogo + serviço de R$ 90, com atalhos para os testes."""

    def __init__(self, client, db, **people):
        self.client = client
        self.db = db
        self.service = people['service']
        self.psych = people['psych']
        self.user = people['user']
        self.user2 = people['user2']

    async def appointment(self, status, user=None, when=APPOINTMENT_AT):
        appointment = models.Appointment(
            id_client=(user or self.user).id,
            id_psychologist=self.psych.id,
            id_service=self.service.id,
            status=status,
            date_time=when,
        )
        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def payment(self, appointment, status, mp_id='123'):
        self.db.add(
            models.Payment(
                id_mercado_pago=mp_id,
                id_appointment=appointment.id,
                amount=SERVICE_PRICE,
                status=status,
            )
        )
        await self.db.commit()

    async def webhook(self, data_id='123', body_id=None):
        return await self.client.post(
            WEBHOOK,
            params={'data.id': data_id},
            json={'type': 'payment', 'data': {'id': body_id or data_id}},
            headers={'x-signature': 'mock', 'x-request-id': 'req-1'},
        )

    @staticmethod
    async def state(appointment_id):
        """Lê o banco com uma sessão NOVA: só enxerga o que foi commitado."""
        async with TestingSessionLocal() as session:
            appointment = await session.get(models.Appointment, appointment_id)
            payments = (
                (
                    await session.execute(
                        select(models.Payment).where(
                            models.Payment.id_appointment == appointment_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            return appointment.status, {p.id_mercado_pago: p.status for p in payments}


@pytest_asyncio.fixture
async def scenario(
    token_client, db_session, service, availability_paymenttest, user_client
):
    user2 = models.User(
        fullname='Outra Pessoa',
        email='outra@example.com',
        password='x',
    )
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)

    return Scenario(
        token_client,
        db_session,
        service=service,
        psych=availability_paymenttest,
        user=user_client,
        user2=user2,
    )


def _mp_returns(mock_payment, appointment_id, *, status='approved', **extra):
    mock_payment.return_value.get.return_value = {
        'status': 200,
        'response': {
            'status': status,
            'transaction_amount': extra.pop('amount', SERVICE_PRICE),
            'external_reference': f'Appointment:{appointment_id}',
            **extra,
        },
    }


@pytest.fixture
def mock_signature():
    with patch(VALIDATOR) as validator:
        validator.return_value = None
        yield validator


@pytest.fixture
def mp():
    with patch(MP_SDK_PAYMENT) as mock_payment:
        yield mock_payment


@pytest.fixture
def flag():
    with patch(FLAG) as flagged:
        yield flagged


@pytest.mark.asyncio
async def test_pending_to_approved_update_is_persisted(scenario, mock_signature, mp):
    """Bug original: atualizar um pagamento já existente não dava commit nem
    confirmava a consulta (PIX/boleto: 1º aviso 'pending', 2º 'approved')."""
    appointment = await scenario.appointment(PENDING)
    await scenario.payment(appointment, PaymentStatus.pending)
    _mp_returns(mp, appointment.id, status='approved')

    response = await scenario.webhook()

    assert response.status_code == HTTPStatus.CREATED
    status, payments = await scenario.state(appointment.id)
    assert payments == {'123': PaymentStatus.approved}
    assert status == CONFIRMED


@pytest.mark.asyncio
async def test_first_notification_approved_confirms_pending(
    scenario, mock_signature, mp
):
    appointment = await scenario.appointment(PENDING)
    _mp_returns(mp, appointment.id)

    response = await scenario.webhook()

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['status'] == 'approved'
    status, payments = await scenario.state(appointment.id)
    assert status == CONFIRMED
    assert payments == {'123': PaymentStatus.approved}


@pytest.mark.asyncio
async def test_approved_payment_never_revives_a_canceled_appointment(
    scenario, mock_signature, mp, flag
):
    appointment = await scenario.appointment(CANCELED)
    _mp_returns(mp, appointment.id)

    response = await scenario.webhook()

    assert response.status_code == HTTPStatus.CREATED
    status, payments = await scenario.state(appointment.id)
    assert status == CANCELED
    assert payments == {'123': PaymentStatus.approved}
    flag.assert_called_once()


@pytest.mark.asyncio
async def test_wrong_amount_or_currency_does_not_confirm(
    scenario, mock_signature, mp, flag
):
    appointment = await scenario.appointment(PENDING)

    _mp_returns(mp, appointment.id, amount=1)
    await scenario.webhook(data_id='111')
    _mp_returns(mp, appointment.id, currency_id='USD')
    await scenario.webhook(data_id='222')

    status, _ = await scenario.state(appointment.id)
    assert status == PENDING
    assert flag.call_count == 2  # noqa: PLR2004


@pytest.mark.asyncio
async def test_rejected_attempt_keeps_pending_and_retry_can_confirm(
    scenario, mock_signature, mp
):
    appointment = await scenario.appointment(PENDING)

    _mp_returns(mp, appointment.id, status='rejected')
    await scenario.webhook(data_id='111')
    status, _ = await scenario.state(appointment.id)
    assert status == PENDING

    _mp_returns(mp, appointment.id, status='approved')
    await scenario.webhook(data_id='222')
    status, payments = await scenario.state(appointment.id)
    assert status == CONFIRMED
    assert payments == {'111': PaymentStatus.rejected, '222': PaymentStatus.approved}


@pytest.mark.asyncio
async def test_failed_extra_attempt_does_not_cancel_a_paid_appointment(
    scenario, mock_signature, mp
):
    appointment = await scenario.appointment(CONFIRMED)

    _mp_returns(mp, appointment.id, status='rejected')
    await scenario.webhook(data_id='999')

    status, _ = await scenario.state(appointment.id)
    assert status == CONFIRMED


@pytest.mark.asyncio
async def test_approved_payment_for_a_taken_slot_is_not_confirmed(
    scenario, mock_signature, mp, flag
):
    mine = await scenario.appointment(PENDING)
    await scenario.appointment(
        CONFIRMED, user=scenario.user2, when=APPOINTMENT_AT + timedelta(minutes=20)
    )
    _mp_returns(mp, mine.id)

    await scenario.webhook()

    status, _ = await scenario.state(mine.id)
    assert status == PENDING
    flag.assert_called_once()


@pytest.mark.asyncio
async def test_refund_cancels_the_confirmed_appointment(
    scenario, mock_signature, mp, flag
):
    appointment = await scenario.appointment(CONFIRMED)
    await scenario.payment(appointment, PaymentStatus.approved)
    _mp_returns(mp, appointment.id, status='refunded')

    await scenario.webhook()

    status, payments = await scenario.state(appointment.id)
    assert status == CANCELED
    assert payments == {'123': PaymentStatus.rejected}


@pytest.mark.asyncio
async def test_duplicate_webhook_delivery_is_idempotent(scenario, mock_signature, mp):
    appointment = await scenario.appointment(PENDING)
    _mp_returns(mp, appointment.id)

    first = await scenario.webhook()
    second = await scenario.webhook()

    assert first.status_code == second.status_code == HTTPStatus.CREATED
    async with TestingSessionLocal() as session:
        total = await session.scalar(select(func.count()).select_from(models.Payment))
    assert total == 1
    status, _ = await scenario.state(appointment.id)
    assert status == CONFIRMED


@pytest.mark.asyncio
async def test_webhook_for_unknown_appointment_does_not_crash(
    scenario, mock_signature, mp, flag
):
    _mp_returns(mp, 424242)

    response = await scenario.webhook()

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['detail'] == 'Consulta não encontrada'


@pytest.mark.asyncio
async def test_body_id_different_from_signed_id_is_rejected(
    scenario, mock_signature, mp
):
    response = await scenario.webhook(data_id='123', body_id='999')

    assert response.status_code == HTTPStatus.BAD_REQUEST
    mp.return_value.get.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_without_signed_data_id_is_ignored(
    token_client, mock_signature, mp
):
    response = await token_client.post(
        WEBHOOK,
        json={'type': 'payment', 'data': {'id': '123'}},
        headers={'x-signature': 'mock', 'x-request-id': 'req-1'},
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['detail'] == 'Evento ignorado'
    mp.return_value.get.assert_not_called()


def _signed_headers(data_id, request_id, ts_ms):
    manifest = f'id:{data_id};request-id:{request_id};ts:{ts_ms};'
    digest = hmac.new(
        settings.MERCADO_PAGO_SECRET.encode(), manifest.encode(), hashlib.sha256
    ).hexdigest()
    return {'x-signature': f'ts={ts_ms},v1={digest}', 'x-request-id': request_id}


@pytest.mark.asyncio
async def test_real_signature_fresh_ok_replayed_and_tampered_rejected(token_client, mp):
    """Usa o validador REAL do Mercado Pago (sem mock) para provar o anti-replay."""
    mp.return_value.get.return_value = {
        'status': 200,
        'response': {'status': 'approved', 'external_reference': 'outro:1'},
    }
    now_ms = int(time.time() * 1000)
    body = {'type': 'payment', 'data': {'id': '123'}}

    async def call(query_id, json, ts_ms):
        return await token_client.post(
            WEBHOOK,
            params={'data.id': query_id},
            json=json,
            headers=_signed_headers('123', 'req-1', ts_ms),
        )

    assert (await call('123', body, now_ms)).status_code == HTTPStatus.CREATED

    ten_minutes_ago = now_ms - 10 * 60 * 1000
    replayed = await call('123', body, ten_minutes_ago)
    assert replayed.status_code == HTTPStatus.UNAUTHORIZED

    other = {'type': 'payment', 'data': {'id': '124'}}
    tampered = await call('124', other, now_ms)
    assert tampered.status_code == HTTPStatus.UNAUTHORIZED

    swapped = await call('123', {'type': 'payment', 'data': {'id': '999'}}, now_ms)
    assert swapped.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_webhook_with_invalid_json_body_is_a_400(token_client, mock_signature):
    response = await token_client.post(
        WEBHOOK,
        params={'data.id': '123'},
        content=b'{nao-e-json',
        headers={'content-type': 'application/json', 'x-signature': 'mock'},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
@pytest.mark.parametrize('status', [CONFIRMED, CANCELED])
async def test_cannot_open_checkout_for_non_pending_appointment(scenario, status):
    appointment = await scenario.appointment(status)

    response = await scenario.client.post(
        '/api/v1/payments', json={'appointment_id': appointment.id}
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Esta consulta não está aguardando pagamento.'


@pytest.mark.asyncio
async def test_cannot_open_checkout_for_expired_or_past_appointment(scenario):
    expired = await scenario.appointment(PENDING)
    expired.created_at = datetime(2026, 5, 10, 23, 0, tzinfo=timezone.utc)
    await scenario.db.commit()

    response = await scenario.client.post(
        '/api/v1/payments', json={'appointment_id': expired.id}
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert 'prazo para pagamento' in response.json()['detail']

    yesterday = datetime(2026, 5, 10, 10, 0, tzinfo=timezone.utc)
    past = await scenario.appointment(PENDING, when=yesterday)
    response = await scenario.client.post(
        '/api/v1/payments', json={'appointment_id': past.id}
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert 'já passou' in response.json()['detail']


@pytest.mark.asyncio
async def test_mercado_pago_failure_becomes_a_clean_502(
    token_client, schedule_payment_pending
):
    with patch(MP_SDK_PREFERENCE) as preference:
        preference.return_value.create.return_value = {'status': 400, 'response': {}}

        response = await token_client.post(
            '/api/v1/payments', json={'appointment_id': schedule_payment_pending.id}
        )

    assert response.status_code == HTTPStatus.BAD_GATEWAY


@pytest.mark.asyncio
async def test_slow_mercado_pago_call_does_not_block_the_event_loop(
    token_client, schedule_payment_pending
):
    """O SDK é síncrono: se rodasse no event loop, TODA a API congelaria."""
    window = {}
    ticks = 0

    def slow_create(_data):
        window['start'] = ticks
        time.sleep(0.3)
        window['end'] = ticks
        return {'status': 201, 'response': {'init_point': 'https://checkout-fake.com'}}

    async def ticker():
        nonlocal ticks
        while True:
            await asyncio.sleep(0)
            ticks += 1

    with patch(MP_SDK_PREFERENCE) as preference:
        preference.return_value.create.side_effect = slow_create
        task = asyncio.create_task(ticker())
        response = await token_client.post(
            '/api/v1/payments', json={'appointment_id': schedule_payment_pending.id}
        )
        task.cancel()

    assert response.status_code == HTTPStatus.CREATED
    assert window['end'] - window['start'] >= 100  # noqa: PLR2004
