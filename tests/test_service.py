import pytest


@pytest.mark.asyncio
async def test_get_all_services(token_client, service):
    response = await token_client.get('/api/v1/services')

    status = 200

    assert response.status_code == status
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_no_services_created(token_client):
    response = await token_client.get('/api/v1/services')

    status = 200

    assert response.status_code == status
    assert response.json() == 'Nenhum serviço encontrado.'


@pytest.mark.asyncio
async def test_get_service(token_client, service):
    response = await token_client.get('/api/v1/service/1')

    status = 200

    assert response.status_code == status
    assert response.json()['id'] == 1
    assert response.json()['name'] == service.name
    assert response.json()['description'] == service.description
    assert response.json()['price'] == service.price
    assert response.json()['duration_minutes'] == service.duration_minutes


@pytest.mark.asyncio
async def test_service_not_found(token_client):
    response = await token_client.get('/api/v1/service/1')

    status = 404

    assert response.status_code == status
    assert response.json()['detail'] == 'Serviço não encontrado.'


@pytest.mark.asyncio
async def test_service_query(token_client, service):
    response = await token_client.get(
        f'/api/v1/services/filter?offset=0&limit=1&name={service.name}&description={service.description}&price={service.price}&duration_minutes={service.duration_minutes}'
    )  # noqa

    status = 200

    assert response.status_code == status
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_service_query_not_found(token_client):
    response = await token_client.get(
        '/api/v1/services/filter?offset=0&limit=1&name=terapia'
    )  # noqa

    status = 404

    assert response.status_code == status
    assert response.json()['detail'] == 'Nenhum serviço encontrado!'


@pytest.mark.asyncio
async def test_filter_ilike_in_name(token_client, service, service2):
    response = await token_client.get(
        '/api/v1/services/filter?offset=0&limit=2&name=Terapia'
    )  # noqa

    status = 200

    services = 2

    assert response.status_code == status
    assert isinstance(response.json(), list)
    assert len(response.json()) == services
    assert response.json()[1]['name'] == 'Terapia Parecida'
