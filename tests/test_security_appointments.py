"""Regressão: IDOR, agenda travada por consultas não pagas, janela de cancelamento
e disponibilidade (auditoria de segurança)."""

from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import pytest

from app import models
from app.api.v1.util.util import cancellation_window_closed
from app.schemas.custom_schema import AppointmentStatus

PASSWORD = 'Senha12@#'
NOW = datetime(2026, 5, 11, 0, 0, tzinfo=timezone.utc)
SLOT = '2026-05-11T12:30:00.000Z'


async def _login_as(client, email):
    client.cookies.clear()
    response = await client.post(
        '/api/v1/login', data={'username': email, 'password': PASSWORD}
    )
    assert response.status_code == HTTPStatus.OK


async def _book(client, psych, service, when=SLOT):
    return await client.post(
        '/api/v1/appointments',
        json={
            'id_psychologist': psych.id,
            'service_id': service.id,
            'date_time': when,
        },
    )


async def _add_appointment(db, psych, service, user, when, status):  # noqa: PLR0913, PLR0917
    appointment = models.Appointment(
        id_client=user.id,
        id_psychologist=psych.id,
        id_service=service.id,
        status=status,
        date_time=when,
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment

@pytest.mark.asyncio
async def test_other_client_cannot_touch_someone_elses_appointment(
    client, db_session, schedule, user_client2
):
    """IDOR: o id da consulta é sequencial; a posse (id_client) precisa ser checada."""
    await _login_as(client, 'user2@example.com')
    appointment_id = schedule.id

    cancel = await client.post(
        '/api/v1/appointments/cancel', json={'id_appointment': appointment_id}
    )
    reschedule = await client.post(
        '/api/v1/appointments/rescheduling',
        json={'id_appointment': appointment_id, 'date_new': '2026-05-20T11:10:00Z'},
    )
    pay = await client.post('/api/v1/payments', json={'appointment_id': appointment_id})

    assert cancel.status_code == HTTPStatus.NOT_FOUND
    assert reschedule.status_code == HTTPStatus.NOT_FOUND
    assert pay.status_code == HTTPStatus.NOT_FOUND

    await db_session.refresh(schedule)
    assert schedule.status == AppointmentStatus.pending
    assert schedule.date_time == datetime(2026, 5, 11, 12, 30, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_client_cannot_read_other_users_data(client, user_client, user_client2):
    await _login_as(client, 'user2@example.com')

    other = await client.get(f'/api/v1/users/{user_client.id}')
    listing = await client.get('/api/v1/users')

    assert other.status_code == HTTPStatus.FORBIDDEN
    assert listing.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_psychologist_cannot_read_or_delete_another_psychologists_records(
    client, Record, user_psych_refresh
):
    await _login_as(client, 'userrefresh@example.com')

    listing = await client.get('/api/v1/medical-records')
    delete = await client.request(
        'DELETE', '/api/v1/medical-record', json={'record_id': Record.id}
    )

    assert listing.status_code == HTTPStatus.OK
    assert listing.json() == {'message': 'Nenhum Prontuário registrado.'}
    assert 'Descrição do prontuário' not in listing.text
    assert delete.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_psychologist_cannot_write_record_for_a_patient_that_is_not_theirs(
    client, schedule, user_client, user_psych_refresh
):
    await _login_as(client, 'userrefresh@example.com')

    response = await client.post(
        '/api/v1/medical-record',
        json={
            'id_user': user_client.id,
            'id_appoiment': schedule.id,
            'description': 'Tentando escrever no prontuário de outro profissional.',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == (
        'Você ainda não teve uma consulta com esse usuário.'
    )


@pytest.mark.asyncio
async def test_fresh_unpaid_appointment_still_blocks_the_slot(
    client, availability, service, schedule, user_client2
):
    await _login_as(client, 'user2@example.com')

    response = await _book(client, availability, service)

    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_expired_unpaid_appointment_no_longer_blocks_the_slot(
    client, db_session, availability, service, schedule
):
    schedule.created_at = NOW - timedelta(minutes=31)
    await db_session.commit()

    other = models.User(fullname='Outra Pessoa', email='outra@example.com')
    other.password = schedule.client.password
    db_session.add(other)
    await db_session.commit()

    await _login_as(client, 'outra@example.com')
    response = await _book(client, availability, service)

    assert response.status_code == HTTPStatus.CREATED


@pytest.mark.asyncio
async def test_confirmed_appointment_blocks_the_slot_even_when_old(
    client, db_session, availability, service, schedule
):
    schedule.status = AppointmentStatus.confirmed
    schedule.created_at = NOW - timedelta(days=5)
    await db_session.commit()

    other = models.User(fullname='Outra Pessoa', email='outra@example.com')
    other.password = schedule.client.password
    db_session.add(other)
    await db_session.commit()

    await _login_as(client, 'outra@example.com')
    response = await _book(client, availability, service)

    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_client_cannot_hold_more_than_the_limit_of_unpaid_appointments(
    db_session, availability, service, user_client, token_client
):
    for day in (12, 13):
        await _add_appointment(
            db_session,
            availability,
            service,
            user_client,
            datetime(2026, 5, day, 11, 10, tzinfo=timezone.utc),
            AppointmentStatus.pending,
        )

    response = await _book(token_client, availability, service, '2026-05-14T11:10:00Z')

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'aguardando pagamento' in response.json()['detail']


@pytest.mark.asyncio
async def test_paid_appointments_do_not_count_against_the_unpaid_limit(
    db_session, availability, service, user_client, token_client
):
    for day in (12, 13):
        await _add_appointment(
            db_session,
            availability,
            service,
            user_client,
            datetime(2026, 5, day, 11, 10, tzinfo=timezone.utc),
            AppointmentStatus.confirmed,
        )

    response = await _book(token_client, availability, service, '2026-05-14T11:10:00Z')

    assert response.status_code == HTTPStatus.CREATED


@pytest.mark.asyncio
async def test_cannot_cancel_or_reschedule_inside_the_notice_window(
    availability, token_client, service, schedule
):
    cancel = await token_client.post(
        '/api/v1/appointments/cancel', json={'id_appointment': schedule.id}
    )
    reschedule = await token_client.post(
        '/api/v1/appointments/rescheduling',
        json={'id_appointment': schedule.id, 'date_new': '2026-05-20T11:10:00Z'},
    )

    assert cancel.status_code == HTTPStatus.BAD_REQUEST
    assert reschedule.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_cannot_cancel_or_reschedule_a_session_that_already_happened(
    db_session, availability, token_client, service, schedule
):
    """Bug original: a janela era contada 24h DEPOIS da consulta."""
    schedule.date_time = NOW - timedelta(hours=2)
    schedule.status = AppointmentStatus.confirmed
    await db_session.commit()

    cancel = await token_client.post(
        '/api/v1/appointments/cancel', json={'id_appointment': schedule.id}
    )
    reschedule = await token_client.post(
        '/api/v1/appointments/rescheduling',
        json={'id_appointment': schedule.id, 'date_new': '2026-05-20T11:10:00Z'},
    )

    assert cancel.status_code == HTTPStatus.BAD_REQUEST
    assert reschedule.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_cannot_reschedule_a_canceled_appointment(
    db_session, availability, token_client, service, schedule
):
    schedule.date_time = NOW + timedelta(days=5)
    schedule.status = AppointmentStatus.canceled
    await db_session.commit()

    response = await token_client.post(
        '/api/v1/appointments/rescheduling',
        json={'id_appointment': schedule.id, 'date_new': '2026-05-20T11:10:00Z'},
    )

    assert response.status_code == HTTPStatus.CONFLICT


def test_notice_window_boundaries():
    assert cancellation_window_closed(NOW + timedelta(hours=24)) is False
    assert cancellation_window_closed(NOW + timedelta(hours=23, minutes=59)) is True
    assert cancellation_window_closed(NOW - timedelta(minutes=1)) is True
    assert cancellation_window_closed(NOW + timedelta(hours=5), min_hours=2) is False


@pytest.mark.asyncio
async def test_old_appointments_do_not_hide_the_psychologist_from_new_searches(
    db_session, availability, service, user_client, token_client
):
    """Bug original: qualquer consulta anterior ao fim da busca excluía o psicólogo."""
    await _add_appointment(
        db_session,
        availability,
        service,
        user_client,
        datetime(2026, 5, 8, 12, 30, tzinfo=timezone.utc),
        AppointmentStatus.confirmed,
    )

    response = await token_client.post(
        '/api/v1/appointments/simulation',
        json={'date_time': '2026-05-12T11:10:00Z', 'service_id': service.id},
    )

    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_simulation_excludes_only_overlapping_appointments(
    availability, service, schedule, token_client
):
    overlapping = await token_client.post(
        '/api/v1/appointments/simulation',
        json={'date_time': '2026-05-11T12:50:00Z', 'service_id': service.id},
    )
    later = await token_client.post(
        '/api/v1/appointments/simulation',
        json={'date_time': '2026-05-11T14:00:00Z', 'service_id': service.id},
    )

    assert overlapping.status_code == HTTPStatus.NOT_FOUND
    assert later.status_code == HTTPStatus.OK
    assert len(later.json()) == 1
