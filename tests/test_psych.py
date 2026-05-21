import pytest


@pytest.mark.asyncio
async def test_psych_creating_availability(token_psych):
    payload = {
        'availabilities': [
            {
                'days_of_the_week': [0, 1, 2, 3],
                'start_time': '08:30:29.441Z',
                'end_time': '10:30:29.441Z',
            }
        ]
    }

    response = await token_psych.post('/api/v1/psych/me/availability', json=payload)  # noqa

    status = 201

    assert response.status_code == status
    assert response.json()['message'] == 'Disponibilidades adicionadas com sucesso!'  # noqa


@pytest.mark.asyncio
async def test_user_not_psych_trying_to_create_an_availability(token_client):
    payload = {
        'availabilities': [
            {
                'days_of_the_week': [0, 1, 2, 3],
                'start_time': '08:30:29.441Z',
                'end_time': '10:30:29.441Z',
            }
        ]
    }

    response = await token_client.post('/api/v1/psych/me/availability', json=payload)  # noqa

    status = 403

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O Usuário não tem permissão para realizar essa ação'
    )  # noqa


@pytest.mark.asyncio
async def test_psych_not_found(token_fakepsych):
    payload = {
        'availabilities': [
            {
                'days_of_the_week': [0, 1, 2, 3],
                'start_time': '08:30:29.441Z',
                'end_time': '10:30:29.441Z',
            }
        ]
    }

    response = await token_fakepsych.post('/api/v1/psych/me/availability', json=payload)  # noqa

    status = 409

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Psicólogo não encontrado! Tente realizar o login novamente'
    )  # noqa


@pytest.mark.asyncio
async def test_availability_has_conflicts_same_time(token_psych, availability):
    payload = {
        'availabilities': [
            {
                'days_of_the_week': [0, 1, 2, 3],
                'start_time': '08:30:29.441Z',
                'end_time': '10:30:29.441Z',
            }
        ]
    }

    response = await token_psych.post('/api/v1/psych/me/availability', json=payload)  # noqa

    status = 400

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Conflito de horário detectado entre 08:30 e 10:30, confira seus horários.'  # noqa
    )


@pytest.mark.asyncio
async def test_availability_has_conflicts_existing_schedule_has_not_ended(
    token_psych, availability
):  # noqa
    payload = {
        'availabilities': [
            {
                'days_of_the_week': [0, 1, 2, 3],
                'start_time': '09:30:29.441Z',
                'end_time': '15:30:29.441Z',
            }
        ]
    }

    response = await token_psych.post('/api/v1/psych/me/availability', json=payload)  # noqa

    status = 400

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Conflito de horário detectado entre 09:30 e 15:30, confira seus horários.'  # noqa
    )


@pytest.mark.asyncio
async def test_availability_has_conflicts_end_time(token_psych, availability):  # noqa
    payload = {
        'availabilities': [
            {
                'days_of_the_week': [0, 1, 2, 3],
                'start_time': '07:30:29.441Z',
                'end_time': '09:30:29.441Z',
            }
        ]
    }

    response = await token_psych.post('/api/v1/psych/me/availability', json=payload)  # noqa

    status = 400

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Conflito de horário detectado entre 07:30 e 09:30, confira seus horários.'  # noqa
    )


@pytest.mark.asyncio
async def test_get_availability_psych(token_psych, availability):
    response = await token_psych.get('/api/v1/psych/me/availability')

    status = 200

    days_of_week = 7

    assert response.status_code == status
    assert isinstance(response.json(), list)
    assert len(response.json()) == days_of_week
    assert 'day_of_the_week' in response.json()[0]
    assert 'start_time' in response.json()[0]
    assert 'end_time' in response.json()[0]
    assert 'day_name' in response.json()[0]


@pytest.mark.asyncio
async def test_delete_avalability_psych(token_psych, availability):
    payload = {
        'days_of_the_week': 0,
        'start_time': '08:10:29.441Z',
        'end_time': '12:30:29.441Z',
    }

    response = await token_psych.request(
        'DELETE', '/api/v1/psych/me/availability', json=payload
    )

    status = 200

    assert response.status_code == status
    assert response.json()['message'] == 'Disponibilidade deletada'


@pytest.mark.asyncio
async def test_trying_to_delete_an_availability_without_having(token_psych):
    payload = {
        'days_of_the_week': 5,
        'start_time': '14:10:29.441Z',
        'end_time': '15:30:29.441Z',
    }

    response = await token_psych.request(
        'DELETE', '/api/v1/psych/me/availability', json=payload
    )

    print(response.json())

    status = 404

    assert response.status_code == status
    assert response.json()['detail'] == 'Nenhuma disponibilidade encontrada.'


@pytest.mark.asyncio
async def test_trying_to_delete_an_availability_without_usin_psych(token_client):
    payload = {
        'days_of_the_week': 0,
        'start_time': '08:10:29.441Z',
        'end_time': '12:30:29.441Z',
    }

    response = await token_client.request(
        'DELETE', '/api/v1/psych/me/availability', json=payload
    )

    status = 403

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Usuário não tem permissão para realizar essa função'
    )  # noqa


@pytest.mark.asyncio
async def test_get_appooinment_in_time_period(token_psych, schedule_psych):
    payload = {'start_date': '2026-05-11', 'end_date': '2026-05-30'}

    response = await token_psych.post(
        '/api/v1/psych/me/stats/appoinment-count', json=payload
    )

    status = 200

    assert response.status_code == status
    assert response.json()['total'] == 1
    assert (
        response.json()['message']
        == 'Total de consultas realizadas entre 2026-05-11 a 2026-05-30'
    )  # noqa


@pytest.mark.asyncio
async def test_get_count_appoinment_but_no_one(token_psych):
    payload = {'start_date': '2026-05-11', 'end_date': '2026-05-30'}

    response = await token_psych.post(
        '/api/v1/psych/me/stats/appoinment-count', json=payload
    )

    status = 200

    assert response.status_code == status
    assert response.json()['total'] == 0
    assert (
        response.json()['message']
        == 'Nenhum dado encontrado no período de 2026-05-11 a 2026-05-30'
    )  # noqa


@pytest.mark.asyncio
async def test_user_try_get_metrics_appoinment(token_client):
    payload = {'start_date': '2026-05-11', 'end_date': '2026-05-30'}

    response = await token_client.post(
        '/api/v1/psych/me/stats/appoinment-count', json=payload
    )

    status = 403

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O usuário não tem permissõa para realizar essa ação.'
    )  # noqa


@pytest.mark.asyncio
async def test_get_rate_metrics(
    db_session, token_psych, schedule_psych, schedule, schedule2
):
    schedule_psych.status = 'confirmed'
    schedule.status = 'canceled'
    await db_session.commit()

    response = await token_psych.get('/api/v1/psych/me/stats/rate-appoinments')

    total_appoinments = 3

    status = 200

    assert response.status_code == status
    assert response.json()['total_appoinments'] == total_appoinments


@pytest.mark.asyncio
async def test_user_try_get_rate_metrics(token_client):
    response = await token_client.get('/api/v1/psych/me/stats/rate-appoinments')

    status = 403

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O usuário não tem permissõa para realizar essa ação.'
    )  # noqa


@pytest.mark.asyncio
async def test_psych_has_no_appoimnet_for_metrics(token_psych):
    response = await token_psych.get('/api/v1/psych/me/stats/rate-appoinments')

    status = 200

    assert response.status_code == status
    assert response.json()['message'] == 'Você não possui nenhum dado de consulta.'


@pytest.mark.asyncio
async def test_get_all_psych(token_client, user_psych):
    response = await token_client.get('/api/v1/psych')

    status = 200

    assert response.status_code == status
    assert response.json()[0]['id'] == user_psych.id
    assert response.json()[0]['fullname'] == user_psych.fullname


@pytest.mark.asyncio
async def test_get_psychs_but_have_no_one(token_client):
    response = await token_client.get('/api/v1/psych')

    status = 404

    assert response.status_code == status
    assert response.json()['detail'] == 'Nenhum psicólogo encontrado.'


@pytest.mark.asyncio
async def test_try_get_psychs_desactive(token_client, user_psych_desactive):
    response = await token_client.get('/api/v1/psych')

    status = 404

    assert response.status_code == status
    assert response.json()['detail'] == 'Nenhum psicólogo encontrado.'


@pytest.mark.asyncio
async def test_create_record(
    token_psych, user_client, service, schedule_psych, schedule
):
    payload = {
        'id_user': f'{user_client.id}',
        'id_appoiment': f'{schedule.id}',
        'description': 'Paciente mostrou uma melhora.',
    }

    response = await token_psych.post('/api/v1/medical-record', json=payload)

    status = 201

    print(response.json())

    assert response.status_code == status
    assert response.json()['id'] == 1
    assert 'format_date_br' in response.json()


@pytest.mark.asyncio
async def test_forbiden_create_record(token_client):
    payload = {
        'id_user': 1,
        'id_appoiment': 5,
        'description': 'Paciente mostrou uma melhora.',
    }

    response = await token_client.post('/api/v1/medical-record', json=payload)

    status = 403

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O usuário não tem permissão para realizar essa ação.'
    )  # noqa


@pytest.mark.asyncio
async def test_user_not_exists_in_medical_record(token_psych):
    payload = {
        'id_user': 50,
        'id_appoiment': 5,
        'description': 'Paciente mostrou uma melhora.',
    }

    response = await token_psych.post('/api/v1/medical-record', json=payload)

    status = 404

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O usuário não encontrado, verifique se o id digitado está correto.'
    )  # noqa


@pytest.mark.asyncio
async def test_appoiment_not_found_in_medical_record(token_psych, user_client):
    payload = {
        'id_user': f'{user_client.id}',
        'id_appoiment': 5,
        'description': 'Paciente mostrou uma melhora.',
    }

    response = await token_psych.post('/api/v1/medical-record', json=payload)

    status = 409

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Você ainda não teve uma consulta com esse usuário.'
    )  # noqa


@pytest.mark.asyncio
async def test_get_all_medical_records(
    token_psych, Record, user_client, service, schedule
):
    response = await token_psych.get('/api/v1/medical-records')

    status = 200

    id_record = 1

    assert response.status_code == status
    assert response.json()[0]['id'] == id_record
    assert response.json()[0]['id_client'] == user_client.id
    assert response.json()[0]['id_service'] == service.id
    assert response.json()[0]['description'] == 'Descrição do prontuário'
    assert response.json()[0]['service_name'] == service.name
    assert 'psych_fullname' in response.json()[0]
    assert 'client_name' in response.json()[0]
    assert 'created_at' in response.json()[0]
    assert 'format_date_br' in response.json()[0]


@pytest.mark.asyncio
async def test_forbiden_try_get_medical_record(token_client):
    response = await token_client.get('/api/v1/medical-records')

    status = 403

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O usuário não tem permissão para realizar essa ação.'
    )  # noqa


@pytest.mark.asyncio
async def test_no_one_medical_record(token_psych):
    response = await token_psych.get('/api/v1/medical-records')

    status = 200

    assert response.status_code == status
    assert response.json()['message'] == 'Nenhum Prontuário registrado.'


@pytest.mark.asyncio
async def test_delete_medical_record(
    token_psych, Record, user_client, service, schedule
):
    payload = {'record_id': f'{Record.id}'}

    response = await token_psych.request(
        'DELETE', '/api/v1/medical-record', json=payload
    )

    status = 204

    assert response.status_code == status


@pytest.mark.asyncio
async def test_record_not_exists(token_psych):
    payload = {'record_id': 20}

    response = await token_psych.request(
        'DELETE', '/api/v1/medical-record', json=payload
    )

    status = 404

    assert response.status_code == status
    assert response.json()['detail'] == 'Prontuário não encontrado.'


@pytest.mark.asyncio
async def test_user_try_delete_record(token_client):
    payload = {'record_id': 20}

    response = await token_client.request(
        'DELETE', '/api/v1/medical-record', json=payload
    )

    status = 403

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O usuário não tem permissão para realizar essa ação.'
    )  # noqa


@pytest.mark.asyncio
async def test_get_psych_next_appoiments(   #noqa
    db_session, token_psych, schedule, service, availability, user_client,
):
    schedule.status = 'confirmed'
    await db_session.commit()

    response = await token_psych.get('/api/v1/psych/me/next-appoiments')

    status = 200

    assert response.status_code == status
    assert isinstance(response.json(), list)
    assert response.json()[0]['client'] is not None


@pytest.mark.asyncio
async def test_no_confirmed_appoiments(token_psych):
    response = await token_psych.get('/api/v1/psych/me/next-appoiments')

    status = 200

    assert response.status_code == status
    assert response.json()['message'] == 'Nenhuma consulta confirmada.'


@pytest.mark.asyncio
async def test_forbiden_get_next_psych_appoiments(token_client):
    response = await token_client.get('/api/v1/psych/me/next-appoiments')

    status = 403

    assert response.status_code == status
    assert response.json()['detail'] == 'O usuário não tem permissõa para realizar essa ação'  #noqa
