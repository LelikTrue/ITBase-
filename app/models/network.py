# Path: app/models/network.py

from typing import TYPE_CHECKING, Optional, List
from sqlalchemy.types import Enum as EnumType
from sqlalchemy import Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device import Device


class NetworkSettings(BaseMixin, Base):
    """
    Модель для хранения сетевых настроек, связанных с устройством.
    """
    __tablename__ = 'network_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Внешний ключ для связи "один-к-одному" с основной таблицей устройств
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), unique=True, nullable=False)

    ip_address: Mapped[Optional[str]] = mapped_column(String(15))
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), unique=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    connection_type: Mapped[Optional[str]] = mapped_column(Enum('access', 'trunk', name='connection_type_enum'), default='access')
    vlan_id: Mapped[Optional[int]] = mapped_column(Integer)
    vlans: Mapped[Optional[List[int]]] = mapped_column(PG_ARRAY(Integer))
    native_vlan: Mapped[Optional[int]] = mapped_column(Integer)
    is_tagged: Mapped[bool] = mapped_column(Boolean, default=False)
    vlan_description: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Внешний ключ для связи с коммутатором (который тоже является устройством)
    switch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('devices.id'))
    switch_port: Mapped[Optional[str]] = mapped_column(String(50))
    location_note: Mapped[Optional[str]] = mapped_column(String(255))
    firewall_profile: Mapped[Optional[str]] = mapped_column(String(255))

    # Оставляем только одно, правильное определение для каждой связи.

    # Связь с "владельцем" этих настроек (основным устройством)
    device: Mapped["Device"] = relationship(
        'Device', 
        back_populates='network_settings', 
        foreign_keys=[device_id]
    )
    
    # Связь с коммутатором, к которому подключено устройство
    # Добавляем remote_side, чтобы SQLAlchemy понимал, с каким полем на "удаленной" стороне (Device) связываться
    switch: Mapped[Optional["Device"]] = relationship('Device', foreign_keys=[switch_id], remote_side="Device.id")

    def __repr__(self):
        return f"<NetworkSettings(id={self.id}, device_id={self.device_id}, ip={self.ip_address})>"