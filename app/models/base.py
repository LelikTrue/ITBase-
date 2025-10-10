# Path: app/models/base.py
 
from datetime import datetime, timezone
from sqlalchemy import DateTime, func, text
from sqlalchemy.orm import declared_attr, Mapped, mapped_column

# Мы больше не создаем здесь Base. Мы импортируем его из единственного источника.
from ..db.database import Base


class BaseMixin:
    """
    Базовый класс-примесь (mixin) для всех моделей с общими полями created_at и updated_at.
    """
    # Если ты хочешь, чтобы имя таблицы генерировалось автоматически (например, Device -> devices),
    # можно добавить это сюда. Если ты указываешь __tablename__ в каждой модели, это не нужно.
    # @declared_attr
    # def __tablename__(cls):
    #     return cls.__name__.lower() + "s"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', now())"),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )