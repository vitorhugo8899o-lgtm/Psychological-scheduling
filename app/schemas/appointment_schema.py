from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, computed_field, field_validator

from app.schemas.custom_schema import AppointmentStatus


class AppointmentCreate(BaseModel):
    id_psychologist: int
    service_id: int
    date_time: datetime

    @field_validator('date_time')
    @classmethod
    def validate_time_is_past(cls, value: datetime):
        br_tz = ZoneInfo('America/Sao_Paulo')

        if value.tzinfo is None:
            raise ValueError('A data precisa conter timezone.')

        requested_time_br = value.astimezone(br_tz)
        now_br = datetime.now(br_tz)

        day_limit = 30
        day_max_br = now_br + timedelta(days=day_limit)

        if requested_time_br < now_br:
            raise ValueError(
                f'O horário não pode estar no passado. Horário {requested_time_br.strftime("%d/%m/%Y %H:%M")}'  # noqa
            )

        if requested_time_br > day_max_br:
            raise ValueError(
                f'A data fornecida ultrapassa a data limite permitida. Data: {requested_time_br.strftime("%d/%m/%Y %H:%M")}'  # noqa
            )

        return value.astimezone(timezone.utc)

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
        dt = self.date_time

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        consult = dt.astimezone(ZoneInfo('America/Sao_Paulo')).replace(
            second=0, microsecond=0
        )
        return consult.strftime('%d/%m/%Y %H:%M')

    model_config = ConfigDict(from_attributes=True)
