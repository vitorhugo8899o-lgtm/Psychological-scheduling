import logging
from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Request
from mercadopago.webhook import (
    InvalidWebhookSignatureError,
    WebhookSignatureValidator,
)

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services.payment_service import (
    prepare_data_for_payment,
    process_update_payment,
)
from app.core.config import settings
from app.redis.limiter import limiter, user_or_ip_key
from app.schemas.payment_schema import PaymentCreate, PaymentResponse

payment_route = APIRouter()


@payment_route.post('/payments', status_code=HTTPStatus.CREATED)
@limiter.limit('6/minute', key_func=user_or_ip_key)
async def create_payment(
    request: Request, db: DBSession, user: CurrentUser, appointment: PaymentCreate
):
    return await prepare_data_for_payment(db, appointment, user.id)


@payment_route.post(
    '/payments/webhook', status_code=201, response_model=PaymentResponse | dict
)
async def mercado_pago_webhook(request: Request, db: DBSession):
    signed_data_id = request.query_params.get('data.id')

    if request.query_params.get('topic') and not signed_data_id:
        return {'success': True, 'detail': 'IPN ignorado'}

    try:
        WebhookSignatureValidator.validate(
            request.headers.get('x-signature'),
            request.headers.get('x-request-id'),
            signed_data_id,
            settings.MERCADO_PAGO_SECRET,
            tolerance_seconds=settings.WEBHOOK_TOLERANCE_SECONDS,
        )
    except InvalidWebhookSignatureError as exc:
        logging.warning(
            'Webhook 401: motivo=%s x_signature=%s x_request_id=%s data_id=%s',
            exc,
            bool(request.headers.get('x-signature')),
            bool(request.headers.get('x-request-id')),
            signed_data_id,
        )
        raise HTTPException(
            status_code=401,
            detail='Invalid webhook signature',
        )

    try:
        body = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail='Corpo da requisição inválido')

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail='Corpo da requisição inválido')

    if not signed_data_id:
        return {'success': True, 'detail': 'Evento ignorado'}

    data = body.get('data')
    body_id = data.get('id') if isinstance(data, dict) else None

    if body_id is not None and str(body_id) != signed_data_id:
        raise HTTPException(
            status_code=400, detail='Identificador do pagamento divergente'
        )

    return await process_update_payment(db, signed_data_id, body.get('type'))