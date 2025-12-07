from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class SlugMixin:
    """
    Миксин для добавления системного идентификатора (slug).
    Гарантирует, что сущность имеет неизменяемый код для привязки логики.
    """
    slug: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Системный идентификатор (неизменяемый)"
    )
