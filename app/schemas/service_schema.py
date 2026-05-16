from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.custom_schema import ServiceOption


class ServiceSchema(BaseModel):
    name: str = Field(min_length=7)
    description: str = Field(min_length=10)
    price: float = Field(ge=50)
    duration_minutes: int = Field(ge=30)

    model_config = ConfigDict(from_attributes=True)

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str):
        space = value.replace(' ', '')
        if not space:
            raise ValueError(
                'O título possui apenas espeços vazios, preencha um título valído.'  # noqa
            )

        return value

    @field_validator('description')
    @classmethod
    def validate_description(cls, value: str):
        space = value.replace(' ', '')
        if not space:
            raise ValueError(
                'Descrição possui apenas espaços vazios, preencha uma descrição valída!'  # noqa
            )

        return value


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    duration_minutes: int

    model_config = ConfigDict(from_attributes=True)


class ServiceQuery(BaseModel):
    option: ServiceOption = Field(default=ServiceOption.AND)
    offset: int = Field(ge=0, default=0)
    limit: int = Field(ge=0, default=5)
    name: str | None = Field(default=None)
    price: float | None = Field(ge=50, default=None)
    duration_minutes: int | None = Field(ge=30, default=None)


class FinancialSchema(BaseModel):
    start_date: date
    end_date: date

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v: date):
        today = date.today()

        min_date = date(today.year - 1, today.month, today.day)
        max_date = date(today.year + 1, today.month, today.day)

        if v < min_date:
            raise ValueError('A data não pode ser inferior a 1 ano.')

        if v > max_date:
            raise ValueError('A data não pode ser superior a 1 ano.')

        return v


class ServiceMetric(BaseModel):
    service_name: str
    total_sales: int
    total_revenue: int

    class Config:
        from_attributes = True


class MetricsFinancial(BaseModel):
    by_service: List[ServiceMetric]
    total_general_revenue: int


class ServiceAppointment(BaseModel):
    name: str
    duration_minutes: int
