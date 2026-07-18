from http import HTTPStatus

from fastapi import APIRouter, Request, HTTPException

from mercadopago.webhook import (
    WebhookSignatureValidator,
    InvalidWebhookSignatureError,
)

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services.payment_service import (
    prepare_data_for_payment,
    process_update_payment,
)
from app.schemas.payment_schema import PaymentCreate, PaymentResponse

from app.core.config import settings

payment_route = APIRouter()


@payment_route.post('/payments', status_code=HTTPStatus.CREATED)
async def create_payment(db: DBSession, user: CurrentUser, appointment: PaymentCreate):
    return await prepare_data_for_payment(db, appointment, user.id)


@payment_route.post(
    '/payments/webhook', status_code=201, response_model=PaymentResponse | dict
)
async def mercado_pago_webhook(request: Request, db: DBSession):
    try:
        WebhookSignatureValidator.validate(
            request.headers.get("x-signature"),
            request.headers.get("x-request-id"),
            request.query_params.get("data.id"),
            settings.MERCADO_PAGO_SECRET,
        )
    except InvalidWebhookSignatureError:
        raise HTTPException(
        status_code=401,
        detail="Invalid webhook signature",
    )

    body = await request.json()

    data_id = body.get('data', {}).get('id')
    event_type = body.get('type')

    return await process_update_payment(db, data_id, event_type)
