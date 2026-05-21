from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(str, Enum):
    client = 'cliente'
    psychologist = 'psychologist'
    adm = 'adm'


class PaymentStatus(str, Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'


class AppointmentStatus(str, Enum):
    pending = 'pending'
    confirmed = 'confirmed'
    canceled = 'canceled'


class Token(BaseModel):
    access_token: str
    token_type: str


class UserLoginResponse(BaseModel):
    email: EmailStr
    fullname: str
    role: str


class LoginSuccess(BaseModel):
    status: str = 'success'
    user: UserLoginResponse


class ServiceOption(str, Enum):
    AND = 'and'
    OR = 'or'


class MessagePrompt(BaseModel):
    message: str = Field(max_length=250)

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        null_caracter = 0
        if len(v.strip()) == null_caracter:
            raise ValueError('Digite uma mensagem valída.')
        return v
