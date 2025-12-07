# Path: app/models/asset_type.py

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device import Device
    from .device_model import DeviceModel


from app.models.mixins import SlugMixin


class AssetType(BaseMixin, Base, SlugMixin):
    __tablename__ = 'assettypes'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    # Префикс, используемый для генерации инвентарных номеров. Например, "NB" для ноутбуков.
    prefix: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    devices: Mapped[list['Device']] = relationship(back_populates='asset_type')
    device_models: Mapped[list['DeviceModel']] = relationship(
        back_populates='asset_type'
    )

    def __repr__(self) -> str:
        return f"<AssetType(id={self.id}, name='{self.name}', prefix='{self.prefix}')>"
