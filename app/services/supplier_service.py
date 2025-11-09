# app/services/supplier_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.services.base_service import BaseService
from app.services import DuplicateCheckMixin, DependencyCheckMixin

class SupplierService(DuplicateCheckMixin, DependencyCheckMixin, BaseService[Supplier, SupplierCreate, SupplierUpdate]):
    """
    Сервис для управления поставщиками со специфичными бизнес-правилами.
    """
    async def create(self, db: AsyncSession, obj_in: SupplierCreate, user_id: int) -> Supplier:
        """
        Создает нового поставщика, предварительно проверив на дубликат по имени.
        """
        await self._check_duplicate(db, "name", obj_in.name)
        # Вызываем универсальный метод create из BaseService
        return await super().create(db, obj_in, user_id)

    async def update(self, db: AsyncSession, obj_id: int, obj_in: SupplierUpdate, user_id: int) -> Supplier | None:
        """
        Обновляет поставщика, предварительно проверив на дубликат по имени.
        """
        await self._check_duplicate(db, "name", obj_in.name, current_id=obj_id)
        # Вызываем универсальный метод update из BaseService
        return await super().update(db, obj_id, obj_in, user_id)

    async def delete(self, db: AsyncSession, obj_id: int, user_id: int) -> Supplier | None:
        """
        Удаляет поставщика, предварительно проверив, не связан ли он с активами.
        """
        await self._check_dependencies(db, Device.supplier_id, obj_id, "активов")
        # Если зависимостей нет, вызываем универсальный метод delete из BaseService
        return await super().delete(db, obj_id, user_id)

# Создаем экземпляр сервиса для использования в API
supplier_service = SupplierService(Supplier)