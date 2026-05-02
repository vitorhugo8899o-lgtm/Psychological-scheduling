import pytest


@pytest.mark.asyncio
async def test_fullname_field_there_is_no_space(client):
    payload = {
        'fullname': 'NomeCompleto',
        'email': 'uber@gmail.com',
        'password': 'Senha12@#',
    }

    req = await client.post('/api/v1/users', json=payload)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == (
        'Value error, O nome completo deve ter ao menos um espaço,'
        ' EX: mariajose sobrenome'
    )


@pytest.mark.asyncio
async def test_short_password_field(client):
    payload = {
        'fullname': 'Nome Completo',
        'email': 'uber@gmail.com',
        'password': 'Senha',
    }

    req = await client.post('/api/v1/users', json=payload)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == (
        'Value error, Senha deve ter no mínimo 8 caracteres'
    )


@pytest.mark.asyncio
async def password_field_does_not_have_uppercase_letter(client):
    payload = {
        'fullname': 'Nome Completo',
        'email': 'uber@gmail.com',
        'password': 'senha12@#',
    }

    req = await client.post('/api/v1/users', json=payload)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == (
        'Value error, Sua senha deve conter pelo menos uma letra maiúscula'
    )


@pytest.mark.asyncio
async def test_password_field_does_not_have_lowercase_letter(client):
    payload = {
        'fullname': 'Nome Completo',
        'email': 'uber@gmail.com',
        'password': 'SENHA12@#',
    }

    req = await client.post('/api/v1/users', json=payload)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == (
        'Value error, Sua senha deve conter pelo menos uma letra minúscula'
    )


@pytest.mark.asyncio
async def test_password_field_does_not_have_special_character(client):
    payload = {
        'fullname': 'Nome Completo',
        'email': 'uber@gmail.com',
        'password': 'Senha1234',
    }

    req = await client.post('/api/v1/users', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, Sua senha deve conter um caracter especial do tipo: @#$%!&?'  # noqa
    )


@pytest.mark.asyncio
async def test_password_field_does_not_have_number(client):
    payload = {
        'fullname': 'Nome Completo',
        'email': 'uber@gmail.com',
        'password': 'SENHAas@#',
    }

    req = await client.post('/api/v1/users', json=payload)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == (
        'Value error, Sua senha deve conter um número'
    )


@pytest.mark.asyncio
async def test_update_field_not_has_enough_characters(token_client):
    new_info = {'email': 'new@email.com', 'password': 'Senha12'}

    req = await token_client.put('/api/v1/users', json=new_info)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == (
        'Value error, Senha deve ter no mínimo 8 caracteres'
    )


@pytest.mark.asyncio
async def test_update_field_does_not_have_uppercase_letter(token_client):
    new_info = {'email': 'new@email.com', 'password': 'senha12@#'}

    req = await token_client.put('/api/v1/users', json=new_info)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == (
        'Value error, Sua senha deve conter pelo menos uma letra maiúscula'
    )


@pytest.mark.asyncio
async def test_update_field_does_not_have_lowercase_letter(token_client):
    new_info = {'email': 'new@email.com', 'password': 'SENHA12@#'}

    req = await token_client.put('/api/v1/users', json=new_info)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == (
        'Value error, Sua senha deve conter pelo menos uma letra minúscula'
    )


@pytest.mark.asyncio
async def test_field_update_not_has_numbers(token_client):
    new_info = {'email': 'new@email.com', 'password': 'Senhaaa@#'}

    req = await token_client.put('/api/v1/users', json=new_info)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == (
        'Value error, Sua senha deve conter um número'
    )


@pytest.mark.asyncio
async def test_update_field_not_special_character(token_client):
    new_info = {'email': 'new@email.com', 'password': 'Senha1234'}

    req = await token_client.put('/api/v1/users', json=new_info)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, Sua senha deve conter um caracter especial do tipo: @#$%!&?'  # noqa
    )
