from datetime import datetime  #noqa

import pytest


@pytest.mark.asyncio
async def test_appointment_create(availability, token_client, service):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T16:16:00.000Z',
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
    assert response['date_time'] == '2026-05-11T16:16:00'
    assert response['status'] == 'pending'
    assert response['datetime_format'] == '11/05/2026 13:16'


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
        'date_time': '2026-05-11T09:30:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 409

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Você já possui uma consulta marcada neste período. Consulta:11/05/2026 às 06:30'  # noqa
    )
