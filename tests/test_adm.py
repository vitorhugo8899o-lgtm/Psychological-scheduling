import pytest


@pytest.mark.asyncio
async def test_user_logout(token_adm, user_client):
    payload = {
        'email': f'{user_client.email}',
        'region': '1',
        'number': '55890',
    }

    req = await token_adm.post('/api/v1/psychologist', json=payload)

    status = 201

    response = req.json()

    assert req.status_code == status
    assert response['user_id'] == user_client.id
    assert response['crp'] == 'CRP 01/55890'
    assert 'id' in response['user']
    assert 'fullname' in response['user']
    assert 'email' in response['user']
    assert response['user']['role'] == 'psychologist'
    assert 'created_at' in response['user']


@pytest.mark.asyncio
async def test_user_not_adm_tries_to_create_psych(token_client):
    payload = {
        'email': 'email@não.existe',
        'region': '1',
        'number': '55890',
    }

    req = await token_client.post('/api/v1/psychologist', json=payload)

    status = 403

    assert req.status_code == status
    assert (
        req.json()['detail'] == 'Usuário não possui permissão para realizar essa ação'
    )  # noqa


@pytest.mark.asyncio
async def test_trying_to_create_a_psych_that_does_not_exist(token_adm, user_psych):  # noqa
    payload = {
        'email': f'{user_psych.email}',
        'region': '1',
        'number': '55890',
    }

    req = await token_adm.post('/api/v1/psychologist', json=payload)

    status = 400

    assert req.status_code == status
    assert req.json()['detail'] == 'Usuário já é psicólogo'


@pytest.mark.asyncio
async def test_creating_psych_but_user_does_not_exist(token_adm):
    payload = {
        'email': 'email@não.existe',
        'region': '1',
        'number': '55890',
    }

    req = await token_adm.post('/api/v1/psychologist', json=payload)

    status = 404

    assert req.status_code == status
    assert (
        req.json()['detail']
        == 'Usuário não encontrado,verifique se digitou corretamente o email'
    )  # noqa


@pytest.mark.asyncio
async def test_creating_service(token_adm):
    payload = {
        'name': 'Terapia de casal',
        'description': 'Terapia realizada com um casal',
        'price': '90.00',
        'duration_minutes': '50',
    }

    req = await token_adm.post('/api/v1/services', json=payload)

    response = req.json()

    status = 201

    price = 90.00

    minutes = 50

    assert req.status_code == status
    assert response['id'] == 1
    assert response['name'] == 'Terapia de casal'
    assert response['description'] == 'Terapia realizada com um casal'
    assert response['price'] == price
    assert response['duration_minutes'] == minutes


@pytest.mark.asyncio
async def test_creating_service_as_user(token_client):
    payload = {
        'name': 'Terapia de casal',
        'description': 'Terapia realizada com um casal',
        'price': '90.00',
        'duration_minutes': '50',
    }

    req = await token_client.post('/api/v1/services', json=payload)

    status = 403

    assert req.status_code == status
    assert req.json()['detail'] == 'Usuário não tem permissão para realizar essa ação'  # noqa


@pytest.mark.asyncio
async def test_service_already_exists(token_adm, service):
    payload = {
        'name': 'Terapia de casal',
        'description': 'Terapia realizada com um casal',
        'price': '90.00',
        'duration_minutes': '50',
    }

    req = await token_adm.post('/api/v1/services', json=payload)

    status = 409

    assert req.status_code == status
    assert req.json()['detail'] == 'Esse serviço já está registrado no banco!'


@pytest.mark.asyncio
async def test_get_financial_metrics(token_adm, service, Payment):
    payload = {'start_date': '2026-05-10', 'end_date': '2026-05-20'}

    response = await token_adm.post('/api/v1/financial-report', json=payload)

    status = 200

    total_sales = 1

    total_general_revenue = '90.00'

    assert response.status_code == status
    assert response.json()['by_service'][0]['service_name'] == 'Terapia de casal'
    assert response.json()['by_service'][0]['total_sales'] == total_sales
    assert response.json()['total_general_revenue'] == total_general_revenue  #noqa


@pytest.mark.asyncio
async def test_user_try_get_financial_metrics(token_client, service, Payment):
    payload = {'start_date': '2026-05-11', 'end_date': '2026-05-20'}

    response = await token_client.post('/api/v1/financial-report', json=payload)

    status = 403

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'O usuário não tem permissão para realizar essa ação'
    )  # noqa


@pytest.mark.asyncio
async def test_get_financial_metrics_but_no_one_registry(token_adm):
    payload = {'start_date': '2026-05-11', 'end_date': '2026-05-20'}

    response = await token_adm.post('/api/v1/financial-report', json=payload)

    print(response.json())

    status = 200

    assert response.status_code == status
    assert (
        response.json()['message']
        == 'Nenhum Relátorio de pagamento para o périodo de 2026-05-11 a 2026-05-20'
    )  # noqa
