# Path: app/models/department.py

from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, UniqueConstraint # <--- ИЗМЕНЕНИЕ
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device import Device
    from .employee import Employee


class Department(BaseMixin, Base):
    __tablename__ = 'departments'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500))

    devices: Mapped[List["Device"]] = relationship(back_populates="department")
    employees: Mapped[List["Employee"]] = relationship(back_populates="department")

    # --- ДОБАВЬ ЭТОТ БЛОК ---
    __table_args__ = (
        UniqueConstraint('name', name='uq_departments_name'),
    )
    # -----------------------