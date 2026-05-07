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
