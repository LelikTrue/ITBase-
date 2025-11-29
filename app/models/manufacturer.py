from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device_model import DeviceModel


class Manufacturer(Base, BaseMixin):
    __tablename__ = 'manufacturers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    device_models: Mapped[list['DeviceModel']] = relationship(
        'DeviceModel', back_populates='manufacturer'
    )

    # --- ДОБАВЬ ЭТОТ БЛОК ---
    __table_args__ = (UniqueConstraint('name', name='uq_manufacturers_name'),)
    # -----------------------
