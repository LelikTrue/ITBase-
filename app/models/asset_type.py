# Path: app/models/asset_type.py

from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device import Device
    from .device_model import DeviceModel


class AssetType(BaseMixin, Base):
    __tablename__ = 'assettypes'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Префикс, используемый для генерации инвентарных номеров. Например, "NB" для ноутбуков.
    prefix: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    devices: Mapped[List["Device"]] = relationship(back_populates="asset_type")
    device_models: Mapped[List["DeviceModel"]] = relationship(back_populates="asset_type")

    def __repr__(self):
        return f"<AssetType(id={self.id}, name='{self.name}', prefix='{self.prefix}')>"