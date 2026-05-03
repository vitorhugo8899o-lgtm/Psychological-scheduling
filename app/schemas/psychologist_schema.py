from typing import ClassVar, Set

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.schemas.user_schema import UserPublic


class PsychologistCreate(BaseModel):
    email: EmailStr
    region: int
    number: int

    VALID_REGIONS: ClassVar[Set[int]] = {
        1, 2, 3, 4, 5, 6, 7, 8, 9,
        10, 11, 12, 13, 14, 15, 16,
        17, 18, 19, 20, 21, 22, 23, 24
    }

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: int) -> int:
        if value not in cls.VALID_REGIONS:
            raise ValueError("Região do CRP inválida")
        return value

    @field_validator("number")
    @classmethod
    def validate_number(cls, value: int) -> int:
        min = 1
        max = 999999
        if value < min or value > max:
            raise ValueError("Número do CRP deve ter entre 1 e 6 dígitos")
        return value

    @property
    def crp_formatado(self) -> str:
        return f"CRP {self.region:02d}/{self.number}"

    model_config = ConfigDict(from_attributes=True)


class PsychologistPublic(BaseModel):
    user_id: int
    crp: str
    user: UserPublic
