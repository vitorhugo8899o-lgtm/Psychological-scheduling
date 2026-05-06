from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, field_validator, computed_field

from app.schemas.custom_schema import AppointmentStatus

class AppointmentCreate(BaseModel):
    id_psychologist: int
    service_id: int
    date_time: datetime

    @field_validator('date_time')
    @classmethod
    def validade_time_is_passad(cls, value: datetime):
        now = datetime.now(timezone.utc)
        if value < now:
            raise ValueError('O horário não pode estar no passado')
        return value

    @field_validator('id_psychologist')
    @classmethod
    def validate_id_psych_is_not_zero(cls, value: int):
        if value <= 0:
            raise ValueError('O id do psicólogo não pode ser 0 ou negativo.')
        return value

    @field_validator('service_id')
    @classmethod
    def validate_id_service_is_not_zero(cls, value: int):
        if value <= 0:
            raise ValueError('O id do serviço não pode ser 0 ou negativo.')
        return value

    model_config = ConfigDict(from_attributes=True)


class ApppointmentResponse(BaseModel):
    id: int
    id_client: int
    id_psychologist: int
    id_service: int
    date_time: datetime
    status: AppointmentStatus

    @computed_field
    @property
    def datetime_format(self) -> str:
        consult = self.date_time.astimezone(
            ZoneInfo("America/Sao_Paulo")
        ).replace(
            second=0, microsecond=0
        )

        return consult.strftime("%d/%m/%Y %H:%M")

    model_config = ConfigDict(from_attributes=True)