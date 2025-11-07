# app/services/employee_service.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Device, Employee
from app.schemas.dictionary import EmployeeCreate, EmployeeUpdate
from app.services.base_service import BaseService
from app.services.exceptions import DeletionError

class EmployeeService(BaseService[Employee, EmployeeCreate, EmployeeUpdate]):
    """
    Сервис для управления сотрудниками.
    Имеет уникальную бизнес-логику:
    - Сортировка по фамилии и имени в get_all().
    - Проверка на дубликаты по двум полям: 'employee_id' и 'email'.
    - Проверка на связанные 'Device' перед удалением.
    """

    async def get_all(self, db: AsyncSession) -> list[Employee]:
        """Переопределяем get_all для кастомной сортировки."""
        stmt = select(self.model).order_by(self.model.last_name, self.model.first_name)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: EmployeeCreate, user_id: int) -> Employee:
        # Уникальная логика: проверка дубликатов по двум полям
        if obj_in.employee_id:
            await self._check_duplicate(db, "employee_id", obj_in.employee_id)
        if obj_in.email:
            await self._check_duplicate(db, "email", obj_in.email)
        
        return await super().create(db, obj_in, user_id)

    async def update(self, db: AsyncSession, obj_id: int, obj_in: EmployeeUpdate, user_id: int) -> Employee | None:
        # Уникальная логика: проверка дубликатов по двум полям
        if obj_in.employee_id:
            await self._check_duplicate(db, "employee_id", obj_in.employee_id, current_id=obj_id)
        if obj_in.email:
            await self._check_duplicate(db, "email", obj_in.email, current_id=obj_id)
            
        return await super().update(db, obj_id, obj_in, user_id)

    async def delete(self, db: AsyncSession, obj_id: int, user_id: int) -> Employee | None:
        related_count = await self._count_related(db, Device.employee_id, obj_id)
        if related_count > 0:
            raise DeletionError(f"Невозможно удалить сотрудника, так как с ним связано {related_count} активов.")
        
        return await super().delete(db, obj_id, user_id)

# Создаем единственный экземпляр сервиса, передавая ему модель
employee_service = EmployeeService(Employee)