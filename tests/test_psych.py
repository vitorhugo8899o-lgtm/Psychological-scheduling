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
