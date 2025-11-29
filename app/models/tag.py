from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device import Device


class Tag(BaseMixin, Base):
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    # Простое текстовое поле для категории. Позволит в будущем добавлять новые.
    category: Mapped[str | None] = mapped_column(String(50))

    devices: Mapped[list['Device']] = relationship(
        secondary='device_tags', back_populates='tags'
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}')>"
