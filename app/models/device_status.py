# Path: app/models/device_status.py

from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Integer, String, UniqueConstraint # <--- ИЗМЕНЕНИЕ
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device import Device

class DeviceStatus(BaseMixin, Base):
    __tablename__ = 'devicestatuses'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # Связь с Device
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="status")

    # --- ДОБАВЬ ЭТОТ БЛОК ---
    __table_args__ = (
        UniqueConstraint('name', name='uq_devicestatuses_name'),
    )
    # -----------------------