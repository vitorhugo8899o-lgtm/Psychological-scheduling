from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from pydantic import BaseModel, computed_field

from app.schemas.custom_schema import PaymentStatus


class PaymentCreate(BaseModel):
    appointment_id: int


class PaymentResponse(BaseModel):
    id_mercado_pago: str
    amount: float
    status: str
    created_at: datetime

    @computed_field
    @property
    def format_datetime(self) -> str:
        dt = self.created_at

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        consult = dt.astimezone(ZoneInfo('America/Sao_Paulo')).replace(
            second=0, microsecond=0
        )
        return consult.strftime('%d/%m/%Y %H:%M')

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
