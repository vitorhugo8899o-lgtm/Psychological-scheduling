from enum import Enum

from pydantic import BaseModel, EmailStr


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
