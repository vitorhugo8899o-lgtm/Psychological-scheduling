from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.custom_schema import PaymentStatus

if TYPE_CHECKING:
    from app.models.appointments_models import Appointment


class Payment(Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(primary_key=True)
    id_mercado_pago: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    id_appointment: Mapped[int] = mapped_column(
        ForeignKey('appointments.id'), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name='payment_status_enum'),
        default=PaymentStatus.pending,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    appointment: Mapped['Appointment'] = relationship(back_populates='payment')
