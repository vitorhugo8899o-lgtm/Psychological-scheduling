"""Regressão: prontuários (regras + auditoria) e relatório financeiro."""

import logging
from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import pytest

from app import models
from app.core.audit import audit_logger
from app.schemas.custom_schema import AppointmentStatus, PaymentStatus

NOW = datetime(2026, 5, 11, 0, 0, tzinfo=timezone.utc)
NOTE = 'Texto clínico confidencial que NUNCA pode ir para o log.'


@pytest.fixture
def audit_log(caplog):
    audit_logger.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger='audit')
    yield caplog
    audit_logger.removeHandler(caplog.handler)


def _payload(user_client, schedule):
    return {
        'id_user': user_client.id,
        'id_appoiment': schedule.id,
        'description': NOTE,
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures('service', 'schedule_psych')
@pytest.mark.parametrize(
    ('status', 'when'),
    [
        (AppointmentStatus.pending, NOW - timedelta(days=1)),
        (AppointmentStatus.canceled, NOW - timedelta(days=1)),
        (AppointmentStatus.confirmed, NOW + timedelta(days=1)),
    ],
)
async def test_record_requires_a_confirmed_session_that_already_started(  # noqa: PLR0913, PLR0917
    db_session, token_psych, user_client, schedule, status, when
):
    schedule.status = status
    schedule.date_time = when
    await db_session.commit()

    response = await token_psych.post(
        '/api/v1/medical-record', json=_payload(user_client, schedule)
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'confirmada' in response.json()['detail']


@pytest.mark.asyncio
@pytest.mark.usefixtures('service', 'schedule_psych')
async def test_record_for_a_realized_session_is_created_and_audited(
    db_session, token_psych, user_client, schedule, audit_log
):
    schedule.status = AppointmentStatus.confirmed
    schedule.date_time = NOW - timedelta(hours=3)
    await db_session.commit()

    response = await token_psych.post(
        '/api/v1/medical-record', json=_payload(user_client, schedule)
    )
    listing = await token_psych.get('/api/v1/medical-records')

    assert response.status_code == HTTPStatus.CREATED
    assert listing.status_code == HTTPStatus.OK
    assert 'action=medical_record.create ' in audit_log.text
    assert 'action=medical_record.list ' in audit_log.text
    assert f'appointment={schedule.id}' in audit_log.text
    assert NOTE not in audit_log.text

@pytest.mark.asyncio
async def test_denied_access_attempts_are_audited(
    client, Record, user_psych_refresh, audit_log
):
    await client.post(
        '/api/v1/login',
        data={'username': 'userrefresh@example.com', 'password': 'Senha12@#'},
    )

    response = await client.request(
        'DELETE', '/api/v1/medical-record', json={'record_id': Record.id}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'action=medical_record.delete_denied' in audit_log.text
    assert f'record={Record.id}' in audit_log.text


@pytest.mark.asyncio
async def test_financial_report_counts_only_approved_payments(
    db_session, token_adm, service, schedule_payment
):
    """Bug original: pagamentos pendentes/recusados entravam na receita."""
    for mp_id, status in (
        ('ok', PaymentStatus.approved),
        ('wait', PaymentStatus.pending),
        ('fail', PaymentStatus.rejected),
    ):
        db_session.add(
            models.Payment(
                id_mercado_pago=mp_id,
                id_appointment=schedule_payment.id,
                amount=90.0,
                status=status,
            )
        )
    await db_session.commit()

    response = await token_adm.post(
        '/api/v1/financial-report',
        json={'start_date': '2026-05-10', 'end_date': '2026-05-20'},
    )

    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body['by_service'][0]['total_sales'] == 1
    assert body['total_general_revenue'] == '90.00'


@pytest.mark.asyncio
async def test_financial_report_without_approved_payments_is_empty(
    db_session, token_adm, service, Payment
):
    response = await token_adm.post(
        '/api/v1/financial-report',
        json={'start_date': '2026-05-10', 'end_date': '2026-05-20'},
    )

    assert response.status_code == HTTPStatus.OK
    assert 'Nenhum Relátorio de pagamento' in response.json()['message']
