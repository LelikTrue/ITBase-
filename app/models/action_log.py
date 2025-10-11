import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.database import Base
from .base import BaseMixin


class ActionLog(Base, BaseMixin):
    __tablename__ = 'actionlog' # SQLAlchemy convention is lowercase

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    user_id: Mapped[int | None] = mapped_column(Integer)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
