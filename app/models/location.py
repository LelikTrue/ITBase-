# Path: app/models/location.py

from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device import Device

class Location(BaseMixin, Base):
    __tablename__ = 'locations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True) # <--- ДОБАВЬ unique=True
    # Добавим поле description для консистентности
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="location")

    __table_args__ = (
        UniqueConstraint('name', name='uq_locations_name'), # <--- ДОБАВЬ ЭТО
    )