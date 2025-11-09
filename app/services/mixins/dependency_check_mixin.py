# /app/services/mixins/dependency_check_mixin.py
"""
Миксин для проверки зависимостей перед удалением записей.

Этот модуль предоставляет функциональность для проверки наличия зависимых записей
перед удалением основной сущности. Особенно полезен для:

- Проверки связанных активов (Device) с показом конкретных названий и инвентарных номеров
- Формирования информативных сообщений об ошибках
- Автоматического определения типов связей SQLAlchemy

Примеры использования:
    >>> # В сервисе отдела
    >>> class DepartmentService(BaseService, DependencyCheckMixin):
    ...     async def delete_department(self, db: AsyncSession, department_id: int):
    ...         # Проверка зависимостей с показом конкретных активов
    ...         await self._check_dependencies(
    ...             db=db,
    ...             related_field=Device.department_id,
    ...             obj_id=department_id,
    ...             related_name="активов"
    ...         )
    ...         # Если зависимостей нет - продолжаем удаление
"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from app.services.exceptions import DeletionError
from app.models import Device


class DependencyCheckMixin:
    """
    Миксин для проверки зависимостей перед удалением записей.
    
    Основные возможности:
    - Автоматическое определение связей с таблицей Device
    - Показ конкретных названий активов и инвентарных номеров
    - Ограничение списка активов (первые 3 + количество остальных)
    - Поддержка различных типов связей SQLAlchemy
    
    Attributes:
        related_field: Поле связи SQLAlchemy (например, Device.department_id)
        obj_id: ID удаляемой записи
        related_name: Название зависимых объектов для обычных сообщений
        
    Note:
        Для Device-зависимостей показывает конкретные активы в формате:
        'Название актива' (инв. 12345), 'Другой актив' (инв. 67890) и еще 2 активов
    """
    
    async def _check_dependencies(
        self,
        db: AsyncSession,
        related_field: Any,
        obj_id: int,
        related_name: str = "объектов"
    ) -> None:
        """
        Проверяет наличие зависимых записей перед удалением.
        
        Args:
            db: Сессия базы данных SQLAlchemy
            related_field: Поле связи SQLAlchemy (например, Device.department_id)
            obj_id: ID удаляемой записи
            related_name: Название зависимых объектов для обычных сообщений
            
        Raises:
            DeletionError: Если найдены зависимые записи
            
        Example:
            >>> await self._check_dependencies(
            ...     db=session,
            ...     related_field=Device.department_id,
            ...     obj_id=department_id,
            ...     related_name="активов"
            ... )
            # Если найдены активы:
            # DeletionError: Невозможно удалить запись, так как с ней связаны активы: 
            # 'Компьютер Dell' (инв. 12345), 'Монитор LG' (инв. 67890) и еще 3 активов.
        """
        related_count = await self._count_related(db, related_field, obj_id)
        if related_count > 0:
            # Проверяем, является ли это поле связанным с Device
            is_device_related = self._is_device_related_field(related_field)
            
            if is_device_related:
                devices = await self._get_related_devices(db, related_field, obj_id)
                device_names = [f"'{device.name}' (инв. {device.inventory_number})" for device in devices[:3]]
                devices_str = ", ".join(device_names)
                if related_count > 3:
                    devices_str += f" и еще {related_count - 3} активов"
                message = f"Невозможно удалить запись, так как с ней связаны активы: {devices_str}."
            else:
                message = f"Невозможно удалить запись, так как с ней связано {related_count} {related_name}."
            
            raise DeletionError(message)
    
    def _is_device_related_field(self, related_field: Any) -> bool:
        """
        Определяет, является ли поле связанным с Device.
        
        Использует несколько методов определения:
        1. Проверка атрибута 'key' поля
        2. Анализ строкового представления поля
        
        Args:
            related_field: Поле SQLAlchemy для проверки
            
        Returns:
            bool: True если поле связано с Device, False иначе
            
        Note:
            Метод устойчив к различным типам полей SQLAlchemy и использует
            комплексную проверку для максимальной точности.
        """
        # Проверяем различные атрибуты поля
        field_str = str(related_field).lower()
        
        # Проверяем ключ поля
        if hasattr(related_field, 'key') and related_field.key:
            if 'device' in related_field.key.lower():
                return True
        
        # Проверяем название таблицы в строковом представлении
        if 'device' in field_str:
            return True
            
        return False
    
    async def _get_related_devices(
        self,
        db: AsyncSession,
        related_field: Any,
        obj_id: int,
        limit: int = 5
    ) -> list[Device]:
        """
        Получает список устройств, связанных с записью.
        
        Args:
            db: Сессия базы данных SQLAlchemy
            related_field: Поле связи SQLAlchemy
            obj_id: ID записи для поиска связанных устройств
            limit: Максимальное количество устройств для получения
            
        Returns:
            list[Device]: Список связанных устройств
            
        Note:
            Используется для получения конкретных устройств при формировании
            информативных сообщений об ошибках удаления.
        """
        from app.models import Device
        
        # Создаем запрос
        query = select(Device).where(related_field == obj_id).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()