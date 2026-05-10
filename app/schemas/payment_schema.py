from datetime import datetime

from pydantic import BaseModel

from app.schemas.custom_schema import PaymentStatus


class PaymentCreate(BaseModel):
    appointment_id: int


class PaymentResponse(BaseModel):
    id: int
    id_mercado_pago: str
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentePreference(BaseModel):
    title: str
    description: str
    unit_price: float

    class Config:
        from_attributes = True


class PaymentDB(BaseModel):
    id_mercado_pago: str
    id_appointment: int
    amount: float
    status: PaymentStatus
