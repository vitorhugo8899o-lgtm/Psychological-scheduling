from http import HTTPStatus

from fastapi import APIRouter, Request

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services.payment_service import (
    prepare_data_for_payment,
    process_update_payment,
)
from app.schemas.payment_schema import PaymentCreate

payment_route = APIRouter()


@payment_route.post('/payments', status_code=HTTPStatus.CREATED)
async def create_payment(db: DBSession, user: CurrentUser, appointment: PaymentCreate):
    return await prepare_data_for_payment(db, appointment, user.id)


@payment_route.post("/payments/webhook")
async def mercado_pago_webhook(request: Request, db: DBSession):
    body = await request.json()
    print(body)

    data_id = body.get("data", {}).get("id")
    event_type = body.get("type")

    return await process_update_payment(db, data_id, event_type)
