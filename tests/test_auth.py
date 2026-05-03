import pytest


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
async def test_email_incorrect(client):
    data = {'username': 'user@example.com', 'password': 'Senha12@#'}

    req = await client.post('/api/v1/login', data=data)

    status = 401

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Email ou senha incorretos!, verifique se digitou corretamente'
    )  # noqa


@pytest.mark.asyncio
async def test_password_incorrect(client, user_client):
    data = {'username': 'user@example.com', 'password': 'Senhaerrada12@#'}

    req = await client.post('/api/v1/login', data=data)

    status = 401

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Email ou senha incorretos!, verifique se digitou corretamente'
    )  # noqa
