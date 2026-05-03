import pytest


@pytest.mark.asyncio
async def test_user_logout(token_adm, user_client):
    payload = {
        'email': f'{user_client.email}',
        'region': '1',
        'number': '55890',
    }

    req = await token_adm.post('/api/v1/psychologist', json=payload)

    status = 201

    response = req.json()

    print(response)

    assert req.status_code == status
    assert response['user_id'] == user_client.id
    assert response['crp'] == 'CRP 01/55890'
    assert 'id' in response['user']
    assert 'fullname' in response['user']
    assert 'email' in response['user']
    assert response['user']['role'] == 'psychologist'
    assert 'created_at' in response['user']
