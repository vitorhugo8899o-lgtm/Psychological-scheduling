from enum import Enum


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