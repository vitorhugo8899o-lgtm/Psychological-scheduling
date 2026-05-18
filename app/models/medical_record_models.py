from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.psychologist_models import Psychologist
    from app.models.service_models import Service
    from app.models.users_models import User


class MedicalRecord(Base):
    __tablename__ = 'medical_records'

    id: Mapped[int] = mapped_column(primary_key=True)
    id_psychologist: Mapped[int] = mapped_column(
        ForeignKey('psychologists.id'), nullable=False
    )
    id_client: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    id_service: Mapped[int] = mapped_column(ForeignKey('services.id'), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    client: Mapped['User'] = relationship(
        back_populates='medical_record_user', foreign_keys=[id_client]
    )

    service: Mapped['Service'] = relationship(back_populates='medical_record')

    psychologist: Mapped['Psychologist'] = relationship(
        back_populates='medical_records'
    )
