# Path: app/models/device_model.py

from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, ForeignKey, UniqueConstraint # <--- ДОБАВЬ UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .manufacturer import Manufacturer
    from .asset_type import AssetType
    from .device import Device


class DeviceModel(BaseMixin, Base):
    __tablename__ = 'devicemodels'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # --- > РЕШЕНИЕ ПРОБЛЕМЫ: НЕДОСТАЮЩИЕ ВНЕШНИЕ КЛЮЧИ < ---
    manufacturer_id: Mapped[int] = mapped_column(ForeignKey('manufacturers.id'), nullable=False)
    asset_type_id: Mapped[int] = mapped_column(ForeignKey('assettypes.id'), nullable=False)

    # --- > ЧИСТЫЕ СВЯЗИ (RELATIONSHIPS) < ---
    manufacturer: Mapped["Manufacturer"] = relationship(back_populates="device_models")
    asset_type: Mapped["AssetType"] = relationship(back_populates="device_models")
    devices: Mapped[List["Device"]] = relationship(back_populates="device_model")

    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    __table_args__ = (
        UniqueConstraint('name', 'manufacturer_id', name='uq_devicemodel_name_manufacturer'),
    )
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    def __repr__(self):
        return f"<DeviceModel(id={self.id}, name='{self.name}')>"