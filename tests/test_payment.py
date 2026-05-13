from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_create_payment(token_client, availability_paymenttest, schedule_payment):
    payload = {'appointment_id': f'{schedule_payment.id}'}

    response = await token_client.post('/api/v1/payments', json=payload)

    status = 201

    assert response.status_code == status
    assert 'checkout_url' in response.json()


@pytest.mark.asyncio
async def test_create_payment_appointment_not_exist(token_client):
    payload = {'appointment_id': 45}

    response = await token_client.post('/api/v1/payments', json=payload)

    status = 404

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Erro ao tentar encontrar a consulta, tente novamente.'
    )  # noqa


@pytest.mark.asyncio
async def test_trying_to_pay_for_another_user_consultation(
    token_adm, availability_paymenttest, schedule_payment
):
    payload = {'appointment_id': f'{schedule_payment.id}'}

    response = await token_adm.post('/api/v1/payments', json=payload)

    status = 404

    assert response.status_code == status
    assert (
        response.json()['detail']
        == 'Erro ao tentar encontrar a consulta, tente novamente.'
    )  # noqa


@patch('app.api.v1.repositories.payment_repo.sdk.payment')
@pytest.mark.asyncio
async def test_webhook(
    mock_payment, token_client, availability_paymenttest, schedule_payment
):

    mock_payment.return_value.get.return_value = {
        'response': {
            'id': '123',
            'status': 'approved',
            'transaction_amount': 90,
            'external_reference': f'Appointment:{schedule_payment.id}',
        }
    }

    payload = {'type': 'payment', 'data': {'id': '123'}}

    response = await token_client.post('/api/v1/payments/webhook', json=payload)

    status = 201

    amount = 90.0

    assert response.status_code == status
    assert response.json()['id_mercado_pago'] == '123'
    assert response.json()['amount'] == amount
    assert response.json()['status'] == 'approved'
    assert 'created_at' in response.json()
    assert response.json()['format_datetime'] == '10/05/2026 21:00'


@patch('app.api.v1.repositories.payment_repo.sdk.payment')
@pytest.mark.asyncio
async def test_webhook_is_not_a_payment_event(
    mock_payment, token_client, availability_paymenttest, schedule_payment
):
    mock_payment.return_value.get.return_value = {
        'response': {
            'id': '123f',
            'status': 'approved',
            'transaction_amount': 90,
            'external_reference': f'Appointment:{schedule_payment.id}',
        }
    }

    payload = {'data': {'id': '123'}}

    response = await token_client.post('/api/v1/payments/webhook', json=payload)

    status = 201

    assert response.status_code == status
    assert True is response.json()['success']
    assert response.json()['detail'] == 'Evento ignorado'


@patch('app.api.v1.repositories.payment_repo.sdk.payment')
@pytest.mark.asyncio
async def test_external_reference_invalid(
    mock_payment, token_client, availability_paymenttest, schedule_payment
):
    mock_payment.return_value.get.return_value = {
        'response': {
            'id': '123',
            'status': 'approved',
            'transaction_amount': 90,
            'external_reference': 'not_appointment:78',
        }
    }

    payload = {'type': 'payment', 'data': {'id': '123'}}

    response = await token_client.post('/api/v1/payments/webhook', json=payload)

    status = 201

    assert response.status_code == status
    assert True is response.json()['success']
    assert response.json()['detail'] == 'Não é um pagamento de consulta'


@patch('app.api.v1.repositories.payment_repo.sdk.payment')
@pytest.mark.asyncio
async def test_payment_cancelled(
    mock_payment, token_client, availability_paymenttest, schedule_payment
):
    mock_payment.return_value.get.return_value = {
        'response': {
            'id': '123',
            'status': 'cancelled',
            'transaction_amount': 90,
            'external_reference': f'Appointment:{schedule_payment.id}',
        }
    }

    payload = {'type': 'payment', 'data': {'id': '123'}}

    response = await token_client.post('/api/v1/payments/webhook', json=payload)

    status = 201

    amount = 90.0

    assert response.status_code == status
    assert response.json()['id_mercado_pago'] == '123'
    assert response.json()['amount'] == amount
    assert 'created_at' in response.json()
    assert response.json()['format_datetime'] == '10/05/2026 21:00'


@patch('app.api.v1.repositories.payment_repo.sdk.payment')
@pytest.mark.asyncio
async def test_payment_pending(
    mock_payment, token_client, availability_paymenttest, schedule_payment
):
    mock_payment.return_value.get.return_value = {
        'response': {
            'id': '123',
            'transaction_amount': 90,
            'external_reference': f'Appointment:{schedule_payment.id}',
        }
    }

    payload = {'type': 'payment', 'data': {'id': '123'}}

    response = await token_client.post('/api/v1/payments/webhook', json=payload)

    status = 201

    amount = 90.0

    assert response.status_code == status
    assert response.json()['id_mercado_pago'] == '123'
    assert response.json()['amount'] == amount
    assert response.json()['status'] == 'pending'
    assert 'created_at' in response.json()
    assert response.json()['format_datetime'] == '10/05/2026 21:00'
