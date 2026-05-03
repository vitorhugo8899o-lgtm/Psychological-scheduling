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


@pytest.mark.asyncio
async def test_update_user(token_client):
    new_info = {'email': 'new@email.com', 'password': 'Senha12@#'}

    req = await token_client.put('/api/v1/users', json=new_info)

    response = req.json()

    status = 200

    assert req.status_code == status
    assert response['email'] == 'new@email.com'
    assert 'id' in response
    assert 'fullname' in response
    assert 'role' in response
    assert 'created_at' in response


@pytest.mark.asyncio
async def test_update_in_use_email(token_client, user_client2):
    payload = {'email': 'user2@example.com', 'password': 'Senha12@#'}

    req = await token_client.put('/api/v1/users', json=payload)

    status = 409

    assert req.status_code == status
    assert req.json()['detail'] == 'Esse endereço de Email já está em uso!'


@pytest.mark.asyncio
async def test_delete_user(token_client):
    req = await token_client.delete('/api/v1/users')

    status = 204

    assert req.status_code == status


@pytest.mark.asyncio
async def test_get_user(user_client, token_adm):
    req = await token_adm.get(f'/api/v1/users/{user_client.id}')

    status = 200

    response = req.json()

    assert req.status_code == status
    assert response['id'] == user_client.id
    assert response['fullname'] == 'Full Name'
    assert response['email'] == user_client.email
    assert response['role'] == user_client.role
    assert 'created_at' in response


@pytest.mark.asyncio
async def test_user_not_adm_tries_to_get_user(user_client, token_client):
    req = await token_client.get(f'/api/v1/users/{user_client.id}')

    status = 403

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Usuário não tem permissão para realizar essa ação'
    )  # noqa


@pytest.mark.asyncio
async def test_trying_to_catch_a_user_that_does_not_exist(token_adm):
    req = await token_adm.get('/api/v1/users/889')

    status = 404

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Usuário não encontrado. Verifique se digitou o id correto!'
    )  # noqa


@pytest.mark.asyncio
async def test_get_users(user_client, user_client2, token_adm):
    req = await token_adm.get('/api/v1/users')

    status = 200

    response = req.json()

    assert req.status_code == status
    assert isinstance(response, list)
    assert len(response) >= 1
    assert 'email' in response[0]
    assert 'created_at' in response[0]
    assert 'fullname' in response[0]
    assert 'id' in response[0]
    assert 'role' in response[0]


@pytest.mark.asyncio
async def test_user_not_adm_tries_to_get_users(token_client):
    req = await token_client.get('/api/v1/users')

    status = 403

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Usuário não tem permissão para realizar essa ação.'
    )  # noqa
