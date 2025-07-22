from datetime import datetime # Still needed for type hints if not using func.now()
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func # Import func

Base = declarative_base()

class BaseMixin:
    """Базовый класс для всех моделей с общими полями."""
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
