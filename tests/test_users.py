import pytest


@pytest.mark.asyncio
async def test_create_user(client):
    payload = {
        'fullname': 'Nome Completo',
        'email': 'uber@gmail.com',
        'password': 'Senha12@#',
    }

    req = await client.post('/api/v1/users', json=payload)

    response = req.json()

    status = 201

    assert req.status_code == status
    assert response['id'] == 1
    assert response['fullname'] == 'Nome Completo'
    assert response['email'] == 'uber@gmail.com'
    assert response['role'] == 'cliente'
    assert 'created_at' in response
