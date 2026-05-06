from datetime import time
from typing import ClassVar, List, Set

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

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
