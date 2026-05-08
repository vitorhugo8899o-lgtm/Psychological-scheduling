from datetime import datetime  # noqa

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
    availability,
    token_client,
    service,
    schedule,
    schedule2
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
    availability,
    token_psych,
    service,
    schedule,
    schedule2
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
