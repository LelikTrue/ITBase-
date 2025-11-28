# /app/services/mixins/duplicate_check_mixin.py
"""
Миксин для проверки дубликатов в моделях.

Этот модуль предоставляет функциональность для проверки уникальности записей
перед созданием или обновлением сущностей. Особенно полезен для:

- Проверки уникальности по одному или нескольким полям
- Игнорирования текущей записи при обновлении
- Формирования понятных сообщений об ошибках валидации

Примеры использования:
    >>> # В сервисе сотрудников
    >>> class EmployeeService(BaseService, DuplicateCheckMixin):
    ...     async def create_employee(self, db: AsyncSession, employee_data):
    ...         # Проверка дубликатов по email
    ...         await self._check_duplicate(
    ...             db=db,
    ...             field_name="email",
    ...             value=employee_data.email,
    ...             error_message="Сотрудник с таким email уже существует"
    ...         )
    ...         # Если дубликатов нет - продолжаем создание
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.exceptions import DuplicateError


class DuplicateCheckMixin:
    """
    Миксин для проверки дубликатов в моделях.

    Основные возможности:
    - Проверка уникальности по одному или нескольким полям
    - Игнорирование текущей записи при обновлении
    - Формирование понятных сообщений об ошибках валидации

    Attributes:
        model: Модель SQLAlchemy для проверки
        field_name: Название поля для проверки уникальности
        value: Значение для проверки
        current_id: ID текущей записи (для игнорирования при обновлении)

    Note:
        Предполагает наличие атрибута `self.model` в сервисе-наследнике,
        который должен ссылаться на модель SQLAlchemy для проверки.
    """

    async def _check_duplicate(
        self,
        db: AsyncSession,
        field_name: str,
        value: Any,
        current_id: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Проверяет наличие дубликатов по указанному полю.

        Args:
            db: Сессия базы данных SQLAlchemy
            field_name: Название поля для проверки уникальности
            value: Значение для проверки
            current_id: ID текущей записи (для игнорирования при обновлении)
            error_message: Кастомное сообщение об ошибке (опционально)

        Raises:
            DuplicateError: Если найден дубликат

        Example:
            >>> await self._check_duplicate(
            ...     db=session,
            ...     field_name="email",
            ...     value="ivan@company.com",
            ...     current_id=employee_id,  # None для создания, ID для обновления
            ...     error_message="Email уже используется другим сотрудником"
            ... )
            # Если найден дубликат:
            # DuplicateError: Email уже используется другим сотрудником

        Note:
            Метод использует атрибут `self.model` для определения модели проверки.
            Убедитесь, что ваш сервис правильно определяет этот атрибут.
        """
        query = select(self.model.id).where(getattr(self.model, field_name) == value)
        if current_id:
            query = query.where(self.model.id != current_id)

        result = await db.execute(query.limit(1))
        if result.scalar_one_or_none() is not None:
            if error_message:
                raise DuplicateError(error_message)
            else:
                raise DuplicateError(
                    f"Запись в '{self.model.__name__}' с таким '{field_name}' уже существует."
                )
