from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.appointments_models import Appointment
    from app.models.avaliabilites_models import Avaliabilite
    from app.models.medical_record_models import MedicalRecord
    from app.models.users_models import User


class Psychologist(Base):
    __tablename__ = 'psychologists'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    crp: Mapped[int] = mapped_column(Text, nullable=False, unique=True)

    user: Mapped['User'] = relationship(
        back_populates='psychologist_profile', uselist=False, lazy='selectin'
    )
    appointments: Mapped[List['Appointment']] = relationship(
        back_populates='psychologist'
    )
    availabilities: Mapped[List['Avaliabilite']] = relationship(
        back_populates='psychologist', cascade='all, delete-orphan'
    )

    medical_records: Mapped[List['MedicalRecord']] = relationship(
        back_populates='psychologist', cascade='all, delete-orphan', lazy='selectin'
    )
