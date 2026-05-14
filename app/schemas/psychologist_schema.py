from datetime import date, datetime, time
from typing import ClassVar, List, Set

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    TypeAdapter,
    computed_field,
    field_serializer,
    field_validator,
)

from app.schemas.user_schema import UserPublic


class PsychologistCreate(BaseModel):
    email: EmailStr
    region: int
    number: int

    VALID_REGIONS: ClassVar[Set[int]] = {
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
    }

    @field_validator('region')
    @classmethod
    def validate_region(cls, value: int) -> int:
        if value not in cls.VALID_REGIONS:
            raise ValueError('Região do CRP inválida')
        return value

    @field_validator('number')
    @classmethod
    def validate_number(cls, value: int) -> int:
        min = 1
        max = 999999
        if value < min or value > max:
            raise ValueError('Número do CRP deve ter entre 1 e 6 dígitos')
        return value

    @property
    def crp_format(self) -> str:
        return f'CRP {self.region:02d}/{self.number}'

    model_config = ConfigDict(from_attributes=True)


class PsychologistPublic(BaseModel):
    user_id: int
    crp: str
    user: UserPublic


class PsychologistAvaliabiliteBlock(BaseModel):
    days_of_the_week: List[int] = Field(description='0 para segunda e 6 para domingo')  # noqa
    start_time: time
    end_time: time

    @field_validator('days_of_the_week')
    @classmethod
    def validate_days_range(cls, values: List[int]) -> List[int]:
        for day in values:
            monday = 0
            sunday = 6
            if day < monday or day > sunday:
                raise ValueError(
                    'O dia da semana deve estar entre 0 (Segunda) e 6 (Domingo)'  # noqa
                )
        return values

    class Config:
        from_attributes = True


class PsychologistAvaliabiliteCreate(BaseModel):
    availabilities: List[PsychologistAvaliabiliteBlock]


class AvailabilityCacheSchema(BaseModel):
    day_of_the_week: int
    start_time: time
    end_time: time

    DAYS_MAP: ClassVar[dict] = {
        0: 'Segunda-feira',
        1: 'Terça-feira',
        2: 'Quarta-feira',
        3: 'Quinta-feira',
        4: 'Sexta-feira',
        5: 'Sábado',
        6: 'Domingo',
    }

    @computed_field
    @property
    def day_name(self) -> str:
        return self.DAYS_MAP.get(self.day_of_the_week, 'Desconhecido')

    @field_serializer('start_time', 'end_time')
    def format_to_user(self, dt_time: time):  # noqa

        return dt_time.strftime('%H:%M')

    class Config:
        from_attributes = True


availability_list_adapter = TypeAdapter(List[AvailabilityCacheSchema])


class DeleteAvailabilySchema(BaseModel):
    days_of_the_week: int
    start_time: time
    end_time: time

    @field_validator('days_of_the_week')
    @classmethod
    def validate_weekday(cls, v):
        monday = 0
        sunday = 6
        if v < monday or v > sunday:
            return ValueError('Digite um dia valido da semana.')
        return v

    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def parse_time(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v[:5], '%H:%M').time()
        return v

    class Config:
        from_attributes = True


class SchemaMetrics(BaseModel):
    start_date: date
    end_date: date

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v: date):
        today = date.today()

        min_date = date(today.year - 10, today.month, today.day)
        max_date = date(today.year + 1, today.month, today.day)

        if v < min_date:
            raise ValueError(
                "A data não pode ser inferior a 10 anos."
            )

        if v > max_date:
            raise ValueError(
                "A data não pode ser superior a 1 ano."
            )

        return v


class ResponseMetrics(BaseModel):
    total: int
    message: str
