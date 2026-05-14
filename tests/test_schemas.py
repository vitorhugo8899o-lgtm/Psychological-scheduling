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
async def test_psychologistcreate_invalid_region(token_adm, user_psych):
    payload = {
        'email': f'{user_psych.email}',
        'region': '51',
        'number': '1564',
    }

    req = await token_adm.post('/api/v1/psychologist', json=payload)

    status = 422

    assert req.status_code == status
    assert req.json()['detail'][0]['msg'] == 'Value error, Região do CRP inválida'  # noqa


@pytest.mark.asyncio
async def test_psychologistcreate_invalid_number(token_adm, user_psych):
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
async def test_psychologistavaliabilite_invalid_day(token_psych):
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


@pytest.mark.asyncio
async def test_appointmentcreate_date_no_timezone(availability, token_client, service):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T11:10:00',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg'] == 'Value error, A data precisa conter timezone.'
    )  # noqa


@pytest.mark.asyncio
async def test_appointmentcreate_date_in_the_past(availability, token_client, service):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2024-05-01T11:10:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, O horário não pode estar no passado. Horário 01/05/2024 08:10'
    )  # noqa


@pytest.mark.asyncio
async def test_date_older_than_30_days_will_generate_an_error(
    availability, token_client, service
):
    payload = {
        'id_psychologist': f'{availability.id}',
        'service_id': f'{service.id}',
        'date_time': '2026-06-10T11:10:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, A data fornecida ultrapassa a data limite permitida. Data: 10/06/2026 08:10'  # noqa
    )


@pytest.mark.asyncio
async def test_schedule_cannot_receive_a_negative_id_from_the_psychologist(
    token_client, service
):
    payload = {
        'id_psychologist': -12,
        'service_id': f'{service.id}',
        'date_time': '2026-05-11T11:10:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, O id do psicólogo não pode ser 0 ou negativo.'
    )  # noqa


@pytest.mark.asyncio
async def test_schedule_cannot_receive_a_negative_id_from_the_service(
    token_client, service
):
    payload = {
        'id_psychologist': 12,
        'service_id': -45,
        'date_time': '2026-05-11T11:10:00Z',
    }

    req = await token_client.post('/api/v1/appointments', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, O id do serviço não pode ser 0 ou negativo.'
    )  # noqa


@pytest.mark.asyncio
async def test_schema_appointment_simulation_has_no_timezone_in_data(token_client):
    payload = {'date_time': '2026-05-11T11:10:00', 'service_id': '1'}

    req = await token_client.post('/api/v1/appointments/simulation', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg'] == 'Value error, A data precisa conter timezone.'
    )


@pytest.mark.asyncio
async def test_schema_appointment_simulation_datetime_past(token_client):
    payload = {'date_time': '2026-05-07T11:10:00Z', 'service_id': '1'}

    req = await token_client.post('/api/v1/appointments/simulation', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, O horário não pode estar no passado. Horário 07/05/2026 08:10'  # noqa
    )


@pytest.mark.asyncio
async def test_appointment_simulation_datetime_deadline(token_client):
    payload = {'date_time': '2026-08-07T11:10:00Z', 'service_id': '1'}

    req = await token_client.post('/api/v1/appointments/simulation', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, A data fornecida ultrapassa a data limite permitida. Data: 07/08/2026 08:10'  # noqa
    )


@pytest.mark.asyncio
async def test_appointment_simulation_service_id_negative_error(token_client):
    payload = {'date_time': '2026-05-15T11:10:00Z', 'service_id': -1}

    req = await token_client.post('/api/v1/appointments/simulation', json=payload)

    status = 422

    assert req.status_code == status
    assert (
        req.json()['detail'][0]['msg']
        == 'Value error, O id do serviço não pode ser 0 ou negativo.'  # noqa
    )


@pytest.mark.asyncio
async def test_date_has_passed_the_minimum_deadline(token_psych):
    payload = {'start_date': '2014-05-11', 'end_date': '2026-05-30'}

    response = await token_psych.post(
        '/api/v1/psych/me/stats/appoinment-count', json=payload
    )

    status = 422

    assert response.status_code == status
    assert (
        response.json()['detail'][0]['msg']
        == 'Value error, A data não pode ser inferior a 10 anos.'
    )  # noqa


@pytest.mark.asyncio
async def test_date_deadline_has_passed(token_psych):
    payload = {'start_date': '2026-05-11', 'end_date': '2028-05-30'}

    response = await token_psych.post(
        '/api/v1/psych/me/stats/appoinment-count', json=payload
    )

    status = 422

    assert response.status_code == status
    assert (
        response.json()['detail'][0]['msg']
        == 'Value error, A data não pode ser superior a 1 ano.'
    )  # noqa
