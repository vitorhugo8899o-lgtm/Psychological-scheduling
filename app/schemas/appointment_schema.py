from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator


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
