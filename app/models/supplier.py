# app/models/supplier.py

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..db.database import Base

class Supplier(Base):
    """Модель Поставщика."""
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, name='{self.name}')>"