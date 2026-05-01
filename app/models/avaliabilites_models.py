from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.psychologist_models import Psychologist


class Avaliabilite(Base):
    __tablename__ = 'avaliabilites'

    id: Mapped[int] = mapped_column(primary_key=True)
    id_psychologist: Mapped[int] = mapped_column(
        ForeignKey('psychologists.id'), nullable=False
    )
    day_of_the_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(
        Time(timezone=True), nullable=False
    )
    end_time: Mapped[time] = mapped_column(Time(timezone=True), nullable=False)

    psychologist: Mapped['Psychologist'] = relationship(
        back_populates='availabilities'
    )
