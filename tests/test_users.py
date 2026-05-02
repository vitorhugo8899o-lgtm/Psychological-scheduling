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


@pytest.mark.asyncio
async def test_email_alredy_in_use(client, user_client):
    payload = {
        'fullname': 'Nome Completo',
        'email': 'user@example.com',
        'password': 'Senha12@#',
    }

    req = await client.post('/api/v1/users', json=payload)

    status = 409

    assert req.status_code == status
    assert req.json()['detail'] == 'Esse endereço de Email já está em uso!'


