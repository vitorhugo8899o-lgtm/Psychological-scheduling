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
async def test_login_user(client, user_client):
    data = {'username': 'user@example.com', 'password': 'Senha12@#'}

    req = await client.post('/api/v1/login', data=data)

    response = req.json()

    status = 200

    assert req.status_code == status
    assert 'Login_info' in req.cookies
    assert response['status'] == 'success'
    assert response['user'] == {
        'email': 'user@example.com',
        'fullname': 'Full Name',
        'role': 'cliente',
    }


@pytest.mark.asyncio
async def test_email_with_invalid_format_login(client):
    data = {'username': 'user@', 'password': 'Senha12@#'}

    req = await client.post('/api/v1/login', data=data)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'] == 'O formato do e-mail enviado é inválido.'


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
