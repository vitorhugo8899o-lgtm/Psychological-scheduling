import hashlib
import hmac
import logging
import time
from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Request

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services.payment_service import (
    prepare_data_for_payment,
    process_update_payment,
)
from app.core.config import settings
from app.redis.limiter import limiter, user_or_ip_key
from app.schemas.payment_schema import PaymentCreate, PaymentResponse

payment_route = APIRouter()

MS_THRESHOLD = 10**11


def _verify_signature(request: Request, secret: str | None, data_id: str | None):
    """Valida o x-signature do Mercado Pago (HMAC-SHA256 + janela de tempo).

    Retorna None se a assinatura é válida, ou o motivo da recusa.
    """
    raw = request.headers.get('x-signature') or ''
    request_id = request.headers.get('x-request-id')

    if not (raw and request_id and data_id and secret):
        return 'cabecalhos_ou_segredo_ausentes'

    parts = {}
    for item in raw.split(','):
        key, sep, value = item.strip().partition('=')
        if sep:
            parts[key] = value

    ts, v1 = parts.get('ts'), parts.get('v1')

    if not (ts and v1):
        return 'x_signature_malformado'

    manifest = f'id:{data_id.lower()};request-id:{request_id};ts:{ts};'
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, v1):
        return 'assinatura_diferente'

    try:
        ts_value = int(ts)
    except ValueError:
        return 'ts_invalido'

    ts_seconds = ts_value / 1000 if ts_value > MS_THRESHOLD else ts_value
    age = abs(time.time() - ts_seconds)

    if age > settings.WEBHOOK_TOLERANCE_SECONDS:
        return f'fora_da_tolerancia(idade={int(age)}s)'

    return None


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

    reason = _verify_signature(request, settings.MERCADO_PAGO_SECRET, signed_data_id)

    if reason:
        logging.warning('Webhook 401: motivo=%s data_id=%s', reason, signed_data_id)
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