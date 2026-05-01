from enum import Enum
from pydantic import BaseModel

class UserRole(str, Enum):
    client = 'cliente'
    psychologist = 'psychologist'


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