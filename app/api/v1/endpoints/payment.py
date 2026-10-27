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

import hashlib
import hmac
import os

payment_route = APIRouter()


def _signature_matches(request: Request, secret: str | None, data_id: str) -> bool:
    raw = request.headers.get('x-signature') or ''
    parts = dict(p.strip().split('=', 1) for p in raw.split(',') if '=' in p)
    ts, v1 = parts.get('ts'), parts.get('v1')

    if not (ts and v1 and secret):
        return False

    manifest = (
        f"id:{data_id.lower()};"
        f"request-id:{request.headers.get('x-request-id')};ts:{ts};"
    )
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(digest, v1)


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
        secret = settings.MERCADO_PAGO_SECRET
        logging.warning(
            'Webhook diag: atual_confere=%s alt_confere=%s tam_atual=%s tem_espaco=%s',
            _signature_matches(request, secret, signed_data_id),
            _signature_matches(request, os.getenv('MERCADO_PAGO_SECRET_ALT'), signed_data_id),
            len(secret or ''),
            (secret or '') != (secret or '').strip(),
        )
        try:
    live_mode = (await request.json()).get('live_mode')
except Exception:
    live_mode = None
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