from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.schemas.custom_schema import AppointmentStatus

if TYPE_CHECKING:
    from app.models.users_models import User
    from app.models.psychologist_models import Psychologist
    from app.models.service_models import Service
    from app.models.paymentes_models import Payment

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_client: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    id_psychologist: Mapped[int] = mapped_column(ForeignKey('psychologists.id'), nullable=False)
    id_service: Mapped[int] = mapped_column(ForeignKey('services.id'), nullable=False)
    date_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(AppointmentStatus, name="appointment_enum_status"),
        default=AppointmentStatus.pending,
        nullable=False
    )

    client: Mapped['User'] = relationship(
        back_populates="appointments_as_client",
        foreign_keys=[id_client]
    )

    psychologist: Mapped['Psychologist'] = relationship(
        back_populates="appointments"
    )

    service: Mapped['Service'] = relationship(
        back_populates="appointments"
    )

    payment: Mapped['Payment'] = relationship(
        back_populates="appointment",
        uselist=False
    )