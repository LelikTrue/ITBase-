# Path: app/models/employee.py

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .department import Department
    from .device import Device


class Employee(BaseMixin, Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # --- > НОВЫЕ ДЕТАЛИЗИРОВАННЫЕ ПОЛЯ < ---
    last_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Фамилия"
    )
    first_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="Имя")
    patronymic: Mapped[str | None] = mapped_column(String(50), comment="Отчество")

    employee_id: Mapped[str | None] = mapped_column(
        String(50), unique=True, index=True, nullable=True, comment="Табельный номер"
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(20))
    position: Mapped[str | None] = mapped_column(String(255), comment="Должность")

    # Внешний ключ
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))

    # Связи
    department: Mapped[Optional["Department"]] = relationship(
        back_populates="employees"
    )
    devices: Mapped[list["Device"]] = relationship(back_populates="employee")

    @property
    def full_name(self) -> str:
        """Возвращает полное имя сотрудника."""
        parts = [self.last_name, self.first_name, self.patronymic]
        return " ".join(part for part in parts if part)

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, full_name='{self.full_name}')>"
