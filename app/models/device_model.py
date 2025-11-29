# Path: app/models/device_model.py

from typing import TYPE_CHECKING

from sqlalchemy import (  # <--- ДОБАВЬ UniqueConstraint
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .asset_type import AssetType
    from .device import Device
    from .manufacturer import Manufacturer


class DeviceModel(BaseMixin, Base):
    __tablename__ = 'devicemodels'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))

    # --- > РЕШЕНИЕ ПРОБЛЕМЫ: НЕДОСТАЮЩИЕ ВНЕШНИЕ КЛЮЧИ < ---
    manufacturer_id: Mapped[int] = mapped_column(
        ForeignKey('manufacturers.id'), nullable=False
    )
    asset_type_id: Mapped[int] = mapped_column(
        ForeignKey('assettypes.id'), nullable=False
    )

    # --- > ЧИСТЫЕ СВЯЗИ (RELATIONSHIPS) < ---
    manufacturer: Mapped['Manufacturer'] = relationship(back_populates='device_models')
    asset_type: Mapped['AssetType'] = relationship(back_populates='device_models')
    devices: Mapped[list['Device']] = relationship(back_populates='device_model')

    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    __table_args__ = (
        UniqueConstraint(
            'name', 'manufacturer_id', name='uq_devicemodel_name_manufacturer'
        ),
    )
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

    def __repr__(self) -> str:
        return f"<DeviceModel(id={self.id}, name='{self.name}')>"
