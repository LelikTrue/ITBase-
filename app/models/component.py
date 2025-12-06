# Path: app/models/component.py

from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin


class Component(BaseMixin, Base):
    __tablename__ = 'components'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False, index=True
    )
    component_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(255), index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255))

    # Polymorphic configuration
    __mapper_args__: ClassVar[dict] = {
        'polymorphic_identity': 'component',
        'polymorphic_on': 'component_type',
    }

    device = relationship('Device', back_populates='components')


class ComponentCPU(Component):
    __tablename__ = 'components_cpu'

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey('components.id', ondelete='CASCADE'), primary_key=True
    )
    cores: Mapped[int] = mapped_column(Integer, nullable=False)
    threads: Mapped[int] = mapped_column(Integer, nullable=False)
    base_clock_mhz: Mapped[int | None] = mapped_column(Integer)

    __mapper_args__: ClassVar[dict] = {
        'polymorphic_identity': 'cpu',
    }


class ComponentRAM(Component):
    __tablename__ = 'components_ram'

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey('components.id', ondelete='CASCADE'), primary_key=True
    )
    size_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    speed_mhz: Mapped[int | None] = mapped_column(Integer)
    form_factor: Mapped[str | None] = mapped_column(String(50))

    __mapper_args__: ClassVar[dict] = {
        'polymorphic_identity': 'ram',
    }


class ComponentStorage(Component):
    __tablename__ = 'components_storage'

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey('components.id', ondelete='CASCADE'), primary_key=True
    )
    type_label: Mapped[str] = mapped_column(String(50), nullable=False)  # SSD, HDD, NVMe
    capacity_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    interface: Mapped[str | None] = mapped_column(String(50))

    __mapper_args__: ClassVar[dict] = {
        'polymorphic_identity': 'storage',
    }


class ComponentGPU(Component):
    __tablename__ = 'components_gpu'

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey('components.id', ondelete='CASCADE'), primary_key=True
    )
    memory_mb: Mapped[int | None] = mapped_column(Integer)

    __mapper_args__: ClassVar[dict] = {
        'polymorphic_identity': 'gpu',
    }


class ComponentMotherboard(Component):
    """Спецификация материнской платы"""
    __tablename__ = 'components_motherboard'

    id: Mapped[int] = mapped_column(
        Integer, ForeignKey('components.id', ondelete='CASCADE'), primary_key=True
    )

    __mapper_args__: ClassVar[dict] = {
        'polymorphic_identity': 'motherboard',
    }


class ComponentHistory(BaseMixin, Base):
    __tablename__ = 'component_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False, index=True
    )
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ADD, REMOVE, UPDATE
    component_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    device = relationship('Device', back_populates='component_history')
