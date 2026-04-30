from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.users_models import User
    from app.models.avaliabilites_models import Avaliabilite
    from app.models.appointments_models import Appointment

class Psychologist(Base):
    __tablename__ = 'psychologists'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    crp: Mapped[int] = mapped_column(Integer, nullable=False)
    
    user: Mapped['User'] = relationship(
        back_populates='psychologist_profile', uselist=False, cascade="all, delete-orphan",
        lazy="selectin"
    )
    appointments: Mapped[List['Appointment']] = relationship(
        back_populates="psychologist"
    )
    availabilities: Mapped[List['Avaliabilite']] = relationship(
        back_populates="psychologist",
        cascade="all, delete-orphan"
    )
