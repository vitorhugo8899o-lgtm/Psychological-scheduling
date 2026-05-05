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


@pytest.mark.asyncio
async def test_service_schema_with_blank_space_in_title(token_adm):
    payload = {
        'name': '          ',
        'description': 'descrição ',
        'price': 50.00,
        'duration_minutes': 50,
    }

    req = await token_adm.post('/api/v1/services', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, O título possui apenas espeços vazios, preencha um título valído.'  # noqa
    )


@pytest.mark.asyncio
async def test_service_schema_with_blank_space_in_description(token_adm):
    payload = {
        'name': 'Terapia de casal',
        'description': '            ',
        'price': 50.00,
        'duration_minutes': 50,
    }

    req = await token_adm.post('/api/v1/services', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, Descrição possui apenas espaços vazios, preencha uma descrição valída!'  # noqa
    )


@pytest.mark.asyncio
async def test_schema_psychologistcreate_invalid_region(token_adm, user_psych):
    payload = {
        'email': f'{user_psych.email}',
        'region': '51',
        'number': '1564',
    }

    req = await token_adm.post('/api/v1/psychologist', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg'] == 'Value error, Região do CRP inválida'
    )  # noqa


@pytest.mark.asyncio
async def test_schema_psychologistcreate_invalid_number(token_adm, user_psych):
    payload = {
        'email': f'{user_psych.email}',
        'region': '10',
        'number': '1564000',
    }

    req = await token_adm.post('/api/v1/psychologist', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, Número do CRP deve ter entre 1 e 6 dígitos'
    )  # noqa


@pytest.mark.asyncio
async def test_schema_psychologistavaliabilite_invalid_day(token_psych):
    payload = {
        'availabilities': [
            {
                'days_of_the_week': [20, 71, 52, 30],
                'start_time': '08:30:29.441Z',
                'end_time': '10:30:29.441Z',
            }
        ]
    }

    req = await token_psych.post('/api/v1/psych/me/availability', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, O dia da semana deve estar entre 0 (Segunda) e 6 (Domingo)'  # noqa
    )
