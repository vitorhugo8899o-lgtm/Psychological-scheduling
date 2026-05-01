from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.custom_schema import UserRole

if TYPE_CHECKING:
    from app.models.appointments_models import Appointment
    from app.models.psychologist_models import Psychologist


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String(1000), nullable=False)
    email: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name='user_role_enum'),
        default=UserRole.client,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    psychologist_profile: Mapped[Optional['Psychologist']] = relationship(
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    appointments_as_client: Mapped[List['Appointment']] = relationship(
        back_populates='client', foreign_keys='Appointment.id_client'
    )
