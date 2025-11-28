# /app/services/mixins/__init__.py
"""
Пакет миксинов для сервисов.

Этот пакет содержит миксины - многократно используемые компоненты,
которые могут быть добавлены к сервисам для расширения их функциональности.

Доступные миксины:
    - DependencyCheckMixin: Проверка зависимостей перед удалением
    - DuplicateCheckMixin: Проверка дубликатов при создании/обновлении

Примеры использования:
    >>> from app.services.mixins import DependencyCheckMixin, DuplicateCheckMixin
    >>>
    >>> class AssetService(BaseService, DependencyCheckMixin, DuplicateCheckMixin):
    ...     # Ваш сервис с поддержкой проверки зависимостей и дубликатов
    ...     pass
"""

from .dependency_check_mixin import DependencyCheckMixin
from .duplicate_check_mixin import DuplicateCheckMixin

__all__ = ["DuplicateCheckMixin", "DependencyCheckMixin"]
