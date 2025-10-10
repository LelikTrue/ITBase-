from typing import TYPE_CHECKING, List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device import Device

class Tag(BaseMixin, Base):
    """Модель для тегов (свойств), описывающих актив. Например: 'Видео', 'PoE'."""
    __tablename__ = 'tags'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Определяем связь с Device через ассоциативную таблицу,
    # которую мы создадим в модели Device.
    devices: Mapped[List["Device"]] = relationship(
        secondary="device_tags",
        back_populates="tags"
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"