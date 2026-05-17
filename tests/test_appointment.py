from datetime import datetime, timezone  # noqa

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_appointment_create(availability, token_client, service):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T12:00:00.000Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    response = req.json()

    status = 201

    id_client = 2

    assert req.status_code == status
    assert response['id'] == 1
    assert response['id_client'] == id_client
    assert response['id_psychologist'] == 1
    assert response['id_service'] == 1
    assert response['date_time'] == '2026-05-11T12:00:00Z'
    assert response['status'] == 'pending'
    assert response['datetime_format'] == '11/05/2026 09:00'


@pytest.mark.asyncio
async def test_clinic_accountscannot_schedule_an_appointment(token_psych):
    payload = {
        'id_psychologist': '12',
        'service_id': '1',
        'date_time': '2026-05-11T12:00:00.000Z',
    }

    req = await token_psych.post('/api/v1/appointments', json=payload)

    status = 403

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'É proibido marcar consultas em contas administrativas da clinica, se desejar marcar uma consulta entre com uma conta normal.'  # noqa
    )


@pytest.mark.asyncio
async def test_service_not_found_in_appointment(availability, token_client):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': '1',
        'date_time': '2026-05-11T16:16:00.000Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 409

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Serviço não encontrado, verifique se digitou corretamente.'
    )  # noqa


@pytest.mark.asyncio
async def test_user_has_appointment(availability, token_client, schedule, service):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T12:30:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 409

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Você já possui uma consulta marcada neste período. Consulta:11/05/2026 às 09:30'  # noqa
    )


@pytest.mark.asyncio
async def test_user_has_appointment_during_that_period_of_time(
    availability, token_client, schedule, service
):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T13:00:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 409

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Você já possui uma consulta marcada neste período. Consulta:11/05/2026 às 09:30'  # noqa
    )


@pytest.mark.asyncio
async def test_scheduling_has_a_non_existent_id_psychologist(token_client, service):
    payload = {
        'id_psychologist': 12,
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T13:00:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 409

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'O Psicólogo não encontrado, verifique se o id digitado é válido'
    )  # noqa


@pytest.mark.asyncio
async def test_psychologist_will_not_be_available_on_the_requested_date(
    availability, token_client, service
):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T15:00:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 409

    assert req.status_code == status
    assert req.json()['detail'] == 'O psicólogo solcitado não atende na data informada.'


@pytest.mark.asyncio
async def test_psychologist_already_has_an_appointment_scheduled_during_this_period(
    availability, token_client, service, schedule_psych
):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T12:30:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 409

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'O psicólogo já possui uma consulta marcada neste horário. Consulta: 11/05/2026 às 09:30'  # noqa
    )


@pytest.mark.asyncio
async def test_appointment_outside_working_hours(availability, token_client, service):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T15:10:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 409

    assert req.status_code == status
    assert req.json()['detail'] == 'O psicólogo solcitado não atende na data informada.'


@pytest.mark.asyncio
async def test_get_appointment_user(
    availability, token_client, service, schedule, schedule2
):
    req = await token_client.get('/api/v1/users/me/appointments')

    status = 200

    response = req.json()

    appointments = 2

    assert req.status_code == status
    assert isinstance(response, list)
    assert len(response) == appointments
    assert response[0]['status'] == 'pending'


@pytest.mark.asyncio
async def test_user_has_no_appointment(token_client):
    req = await token_client.get('/api/v1/users/me/appointments')

    status = 404

    assert req.status_code == status
    assert req.json()['detail'] == 'Nenhuma consulta encontrada.'


@pytest.mark.asyncio
async def test_get_appointment_psych(
    availability, token_psych, service, schedule, schedule2
):
    req = await token_psych.get('/api/v1/psych/me/appointments')

    status = 200

    response = req.json()

    appointments = 2

    assert req.status_code == status
    assert isinstance(response, list)
    assert len(response) == appointments
    assert response[0]['status'] == 'pending'


@pytest.mark.asyncio
async def test_get_appointment_psych_by_a_user_who_is_not(token_client):
    req = await token_client.get('/api/v1/psych/me/appointments')

    status = 403

    assert req.status_code == status
    assert req.json()['detail'] == 'Somente psicólogos podem acessar essa função.'


@pytest.mark.asyncio
async def test_psych_has_no_appointments(token_psych):
    req = await token_psych.get('/api/v1/psych/me/appointments')

    status = 404

    assert req.status_code == status
    assert req.json()['detail'] == 'Nenhuma consulta encontrada.'


@pytest.mark.asyncio
async def test_simulation_appointment(availability, service, token_client):
    payload = {'date_time': '2026-05-12T11:10:00Z', 'service_id': f'{service.id}'}

    req = await token_client.post('/api/v1/appointments/simulation', json=payload)

    status = 200

    assert req.status_code == status
    assert isinstance(req.json(), list)
    assert len(req.json()) == 1
    assert req.json()[0]['id'] == 1
    assert req.json()[0]['fullname'] == 'Full Name'
    assert req.json()[0]['crp'] == 'CRP 01/5596'


@pytest.mark.asyncio
async def test_simulation_appointment_it_should_not_overlap(
    availability, availability2, token_client, service
):
    payload = {'date_time': '2026-05-12T13:10:00Z', 'service_id': f'{service.id}'}

    req = await token_client.post('/api/v1/appointments/simulation', json=payload)

    status = 200

    assert req.status_code == status
    assert isinstance(req.json(), list)
    assert len(req.json()) == 1


@pytest.mark.asyncio
async def test_simulation_appointment_service_id_nnot_found(token_client):
    payload = {'date_time': '2026-05-12T13:10:00Z', 'service_id': 78}

    req = await token_client.post('/api/v1/appointments/simulation', json=payload)

    status = 404

    assert req.status_code == status
    assert req.json()['detail'] == 'Serviço não encontrado.'


@pytest.mark.asyncio
async def test_no_psychologists_available_on_that_date(
    availability, token_client, service
):
    payload = {'date_time': '2026-05-12T18:10:00Z', 'service_id': f'{service.id}'}

    req = await token_client.post('/api/v1/appointments/simulation', json=payload)

    status = 404

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Nehuma disponibilidade para a data: 12/05/2026 às 15:10'
    )  # noqa


@patch('app.api.v1.services.appoint_service.time_passed')
@pytest.mark.asyncio
async def test_reschedule_an_appointment(
    mock_time_passed, availability, token_client, service, schedule_refresh
):

    mock_time_passed.return_value = False

    payload = {
        'id_appointment': f'{schedule_refresh.id}',
        'date_new': '2026-05-12T15:00:00Z',
    }

    response = await token_client.post(
        '/api/v1/appointments/rescheduling', json=payload
    )

    status = 200

    assert response.status_code == status
    assert response.json()['id'] == 1
    assert 'id_client' in response.json()
    assert 'id_psychologist' in response.json()
    assert response.json()['id_service'] == 1
    assert 'date_time' in response.json()
    assert response.json()['status'] == 'confirmed'
    assert response.json()['datetime_format'] == '12/05/2026 12:00'


@pytest.mark.asyncio
async def test_try_to_reschedule_an_appointment_but_any_available_dates(token_client):
    payload = {
        'id_appointment': 50,
        'date_new': '2026-05-12T15:00:00Z',
    }

    response = await token_client.post(
        '/api/v1/appointments/rescheduling', json=payload
    )

    status = 404

    assert response.status_code == status
    assert response.json()['detail'] == 'Consulta não encontrada.'


@patch('app.api.v1.services.appoint_service.time_passed')
@pytest.mark.asyncio
async def test_try_to_reschedule_but_time_passed(
    mock_time_passed, availability, token_client, service, schedule_refresh
):

    mock_time_passed.return_value = True

    payload = {
        'id_appointment': f'{schedule_refresh.id}',
        'date_new': '2026-05-12T15:00:00Z',
    }

    response = await token_client.post(
        '/api/v1/appointments/rescheduling', json=payload
    )

    status = 400

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Já se passaram 24 horas desde o momento em que a consulta foi marcada.'
    )  # noqa


@patch('app.api.v1.services.appoint_service.time_passed')
@pytest.mark.asyncio
async def test_try_to_reschedule_but_conflit_date(
    mock_time_passed, availability, token_client, service, schedule_refresh
):

    mock_time_passed.return_value = False

    payload = {
        'id_appointment': f'{schedule_refresh.id}',
        'date_new': '2026-05-11T14:00:00Z',
    }

    response = await token_client.post(
        '/api/v1/appointments/rescheduling', json=payload
    )

    status = 409

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Você já possui uma consulta marcada neste período. Consulta:11/05/2026 às 11:30'  # noqa
    )


@patch('app.api.v1.services.appoint_service.time_passed')
@pytest.mark.asyncio
async def test_try_to_reschedule_but_psych_not_available_on_this_date(
    mock_time_passed, availability, token_client, service, schedule_refresh
):

    mock_time_passed.return_value = False

    payload = {
        'id_appointment': f'{schedule_refresh.id}',
        'date_new': '2026-05-18T20:00:00Z',
    }

    response = await token_client.post(
        '/api/v1/appointments/rescheduling', json=payload
    )

    status = 409

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O psicólogo solcitado não atende na data informada.'  # noqa
    )


@patch('app.api.v1.services.appoint_service.time_passed')
@pytest.mark.asyncio
async def test_try_to_reschedule_but_psych_has_appointments_available(  # noqa
    mock_time_passed,
    availability,
    token_client,
    service,
    schedule_refresh2,
    schedule_refresh,
):

    mock_time_passed.return_value = False

    payload = {
        'id_appointment': f'{schedule_refresh.id}',
        'date_new': '2026-05-11T15:20:00Z',
    }

    response = await token_client.post(
        '/api/v1/appointments/rescheduling', json=payload
    )

    status = 409

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O psicólogo já possui uma consulta marcada neste horário. Consulta: 11/05/2026 às 12:20'  # noqa
    )


@pytest.mark.asyncio
async def test_cancel_appoinment(availability, token_client, service, schedule):
    payload = {'id_appointment': f'{schedule.id}'}

    response = await token_client.post('/api/v1/appointments/cancel', json=payload)

    stauts = 200

    assert response.status_code == stauts
    assert response.json()['status'] == 'canceled'


@pytest.mark.asyncio
async def test_cancel_appoinment_not_found(token_client):
    payload = {'id_appointment': 15}

    response = await token_client.post('/api/v1/appointments/cancel', json=payload)

    stauts = 404

    assert response.status_code == stauts
    assert (
        response.json()['detail']
        == 'Consulta não encontrada, verifique em sua Aba se realmente possui uma consulta'  # noqa
    )


@pytest.mark.asyncio
async def test_appoinment_already_cancelled(
    db_session, availability, token_client, service, schedule
):
    schedule.status = 'canceled'
    await db_session.commit()

    payload = {'id_appointment': f'{schedule.id}'}

    response = await token_client.post('/api/v1/appointments/cancel', json=payload)

    status = 409

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Esta consulta já foi cancelada, verifique na sua Aba de consultas.'
    )  # noqa


@pytest.mark.asyncio
async def test_appoinment_cancel_time_passed(
    db_session, availability, token_client, service, schedule
):
    schedule.date_time = datetime(2026, 5, 9, 12, 30, tzinfo=timezone.utc)
    await db_session.commit()

    payload = {'id_appointment': f'{schedule.id}'}

    response = await token_client.post('/api/v1/appointments/cancel', json=payload)

    status = 400

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O tempo para cancelamento da consulta já passou, se desejar um reembolso busque na aba de consulta ao lado'  # noqa
    )


@pytest.mark.asyncio
async def test_try_get_the_next_user_appoimnets(
    db_session, availability, token_client, service, schedule
):
    schedule.status = 'confirmed'
    await db_session.commit()

    response = await token_client.get('/api/v1/users/me/next-appointments')

    status = 200

    duration_minutes = 50

    assert response.status_code == status
    assert response.json()[0]['id'] == 1
    assert 'date_time' in response.json()[0]
    assert response.json()[0]['status'] == 'confirmed'
    assert response.json()[0]['service']['name'] == 'Terapia de casal'
    assert response.json()[0]['service']['duration_minutes'] == duration_minutes
    assert response.json()[0]['psychologist']['crp'] == 'CRP 01/5596'
    assert response.json()[0]['psychologist']['user']['fullname'] == 'Full Name'
    assert response.json()[0]['format_date'] == '11/05/2026 às 12h:30'


@pytest.mark.asyncio
async def test_exception_forbiden_get_the_next_appoimnets(token_adm):
    response = await token_adm.get('/api/v1/users/me/next-appointments')

    status = 403

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O usuário não tem permissão para realizar essa ação'
    )  # noqa


@pytest.mark.asyncio
async def test_no_confirmed_appointments(token_client):
    response = await token_client.get('/api/v1/users/me/next-appointments')

    status = 200

    assert response.status_code == status
    assert response.json()['message'] == 'Você não possui nenhuma consulta marcada.'


@pytest.mark.asyncio
async def test_no_confirmed_appointments_status(
    availability, token_client, service, schedule
):
    response = await token_client.get('/api/v1/users/me/next-appointments')

    status = 200

    assert response.status_code == status
    assert response.json()['message'] == 'Você não possui nenhuma consulta marcada.'
