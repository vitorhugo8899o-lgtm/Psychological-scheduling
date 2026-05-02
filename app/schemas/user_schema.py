import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserCreate(BaseModel):
    fullname: str = Field(max_length=1000)
    email: EmailStr = Field(max_length=50)
    password: str = Field(min_length=8, max_length=128)

    @field_validator('fullname')
    def validate_fullname(cls, v: str):
        clean_name = v.replace(' ', '')
        if clean_name == v:
            raise ValueError(
                'O nome completo deve ter ao menos um espaço,'
                ' EX: mariajose sobrenome'
            )

        return v

    @field_validator('password')
    def validate_password(cls, v: str):
        num = 8
        if len(v) < num:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')

        if not re.search(r'[a-z]', v):
            raise ValueError(
                'Sua senha deve conter pelo menos uma letra minúscula'
            )

        if not re.search(r'[A-Z]', v):
            raise ValueError(
                'Sua senha deve conter pelo menos uma letra maiúscula'
            )

        if not re.search(r'\d', v):
            raise ValueError('Sua senha deve conter um número')

        if not re.search(r'[@$!%*?&]', v):
            raise ValueError(
                'Sua senha deve conter um caracter especial do tipo: @#$%!&?'
            )

        return v


class UserPublic(BaseModel):
    id: int
    fullname: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
