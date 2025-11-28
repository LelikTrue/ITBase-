# Path: app/models/device.py

from datetime import date
from typing import TYPE_CHECKING, Any, Optional

# 1. Добавляем импорты для создания ассоциативной таблицы
from sqlalchemy import (
    JSON,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .asset_type import AssetType
    from .attachment import Attachment
    from .department import Department
    from .device_model import DeviceModel
    from .device_status import DeviceStatus
    from .employee import Employee
    from .location import Location
    from .network import NetworkSettings

    # НОВОЕ: Импортируем Supplier для создания связи
    from .supplier import Supplier

    # 2. Импортируем нашу новую модель
    from .tag import Tag

# 3. Создаем АССОЦИАТИВНУЮ ТАБЛИЦУ для связи Device <-> Tag
# Эта таблица будет состоять только из двух внешних ключей.
device_tags_table = Table(
    "device_tags",
    Base.metadata,
    Column(
        "device_id",
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Device(BaseMixin, Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # !# ИЗМЕНЕНИЕ: Добавляем поле для названия актива
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    inventory_number: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    # Серийные и MAC-адреса должны быть уникальными, если они указаны
    serial_number: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    mac_address: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="purchase", default="purchase"
    )
    purchase_date: Mapped[date | None] = mapped_column(Date)
    warranty_end_date: Mapped[date | None] = mapped_column(Date)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    expected_lifespan_years: Mapped[int | None] = mapped_column(Integer)
    current_wear_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2))
    attributes: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Оставляем только одно определение для network_settings
    network_settings: Mapped[Optional["NetworkSettings"]] = relationship(
        "NetworkSettings",
        back_populates="device",
        uselist=False,
        cascade="all, delete-orphan",
        # Явно указываем SQLAlchemy, что эта связь использует ВНЕШНИЙ ключ
        foreign_keys="NetworkSettings.device_id",
    )

    # ForeignKey должен ссылаться на 'имя_таблицы.имя_колонки', а не 'ИмяКласса.id'.
    # Имена таблиц, как правило, в нижнем регистре и во множественном числе.
    device_model_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devicemodels.id"), nullable=False
    )
    asset_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assettypes.id"), nullable=False
    )
    status_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devicestatuses.id"), nullable=False
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.id")
    )
    location_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("locations.id"))
    employee_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("employees.id"))
    # НОВОЕ: Связь с Supplier (один-ко-многим)
    supplier_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("suppliers.id"))

    # Приводим `back_populates` к единому стилю для предсказуемости.
    # Убедись, что в связанных моделях (Department, Location, Employee)
    # есть поле `devices = relationship("Device", back_populates="...")`.
    device_model: Mapped["DeviceModel"] = relationship(
        "DeviceModel", back_populates="devices"
    )
    asset_type: Mapped["AssetType"] = relationship(
        "AssetType", back_populates="devices"
    )
    status: Mapped["DeviceStatus"] = relationship(
        "DeviceStatus", back_populates="devices"
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="devices"
    )
    location: Mapped[Optional["Location"]] = relationship(
        "Location", back_populates="devices"
    )
    employee: Mapped[Optional["Employee"]] = relationship(
        "Employee", back_populates="devices"
    )
    # НОВОЕ: Связь с Supplier. back_populates можно будет добавить в Supplier позже, если понадобится обратная связь.
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier")

    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="device"
    )

    # 4. Добавляем новую связь "многие-ко-многим" с тегами
    tags: Mapped[list["Tag"]] = relationship(
        secondary=device_tags_table, back_populates="devices"
    )
