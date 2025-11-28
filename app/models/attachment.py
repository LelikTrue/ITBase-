# Path: app/models/attachment.py

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base
from .base import BaseMixin

if TYPE_CHECKING:
    from .device import Device


class Attachment(BaseMixin, Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id"), nullable=False
    )

    device: Mapped["Device"] = relationship("Device", back_populates="attachments")
