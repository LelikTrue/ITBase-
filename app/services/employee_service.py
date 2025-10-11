
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, Employee
from app.schemas.dictionary import EmployeeCreate, EmployeeUpdate
from app.services.audit_log_service import log_action

from .base_dictionary_service import BaseDictionaryService
from .exceptions import DeletionError, DuplicateError


class EmployeeService(BaseDictionaryService):
    """
    Сервис для бизнес-логики, связанной с сотрудниками.
    Наследует от BaseDictionaryService, но переопределяет методы
    для обработки уникальных полей (employee_id, email).
    """
    def __init__(self):
        super().__init__(
            model=Employee,
            entity_name_russian='Сотрудник'
        )

    async def get_all(self, db: AsyncSession) -> list[Employee]:
        """Получает всех сотрудников, отсортированных по фамилии и имени."""
        stmt = select(Employee).order_by(Employee.last_name, Employee.first_name)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def _check_duplicates(self, db: AsyncSession, employee_id: str | None, email: str | None, item_id: int | None = None):
        """Проверяет дубликаты по табельному номеру ИЛИ email."""
        if not employee_id and not email:
            return

        conditions = []
        if employee_id:
            conditions.append(Employee.employee_id == employee_id)
        if email:
            conditions.append(Employee.email == email)

        stmt = select(Employee).where(or_(*conditions))

        if item_id:
            stmt = stmt.where(Employee.id != item_id)

        result = await db.execute(stmt)
        existing_item = result.scalars().first()

        if existing_item:
            if employee_id and existing_item.employee_id == employee_id:
                raise DuplicateError(f"Сотрудник с табельным номером '{employee_id}' уже существует.")
            if email and existing_item.email == email:
                raise DuplicateError(f"Сотрудник с email '{email}' уже существует.")

    async def create(self, db: AsyncSession, data: EmployeeCreate, user_id: int) -> Employee:
        """Создает нового сотрудника с проверкой на дубликаты."""
        await self._check_duplicates(db, data.employee_id, data.email)

        try:
            new_item = self.model(**data.model_dump())
            db.add(new_item)
            await db.flush()

            await log_action(
                db=db, user_id=user_id, action_type='create',
                entity_type=self.entity_name_for_log, entity_id=new_item.id,
                details={'full_name': f'{new_item.last_name} {new_item.first_name}'}
            )
            await db.commit()
            await db.refresh(new_item)
            return new_item
        except Exception:
            await db.rollback()
            raise

    async def update(self, db: AsyncSession, item_id: int, data: EmployeeUpdate, user_id: int) -> Employee | None:
        """Обновляет данные сотрудника."""
        await self._check_duplicates(db, data.employee_id, data.email, item_id)

        db_item = await db.get(self.model, item_id)
        if not db_item:
            return None

        try:
            old_values = {
                'last_name': db_item.last_name, 'first_name': db_item.first_name,
                'patronymic': db_item.patronymic, 'employee_id': db_item.employee_id,
                'email': db_item.email, 'phone_number': db_item.phone_number
            }

            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_item, key, value)

            new_values = {
                'last_name': db_item.last_name, 'first_name': db_item.first_name,
                'patronymic': db_item.patronymic, 'employee_id': db_item.employee_id,
                'email': db_item.email, 'phone_number': db_item.phone_number
            }

            await log_action(
                db=db, user_id=user_id, action_type='update',
                entity_type=self.entity_name_for_log, entity_id=db_item.id,
                details={'old': old_values, 'new': new_values}
            )
            await db.commit()
            await db.refresh(db_item)
            return db_item
        except Exception:
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, item_id: int, user_id: int) -> Employee | None:
        """Удаляет сотрудника, если он не привязан к активам."""
        db_item = await db.get(self.model, item_id)
        if not db_item:
            return None

        devices_count = await db.scalar(
            select(func.count(Device.id)).where(Device.employee_id == item_id)
        )
        if devices_count > 0:
            raise DeletionError(f"Нельзя удалить сотрудника '{db_item.last_name}'. За ним числится {devices_count} устройств.")

        try:
            employee_name = f'{db_item.last_name} {db_item.first_name}'
            await db.delete(db_item)
            await log_action(
                db=db, user_id=user_id, action_type='delete',
                entity_type=self.entity_name_for_log, entity_id=item_id,
                details={'name': employee_name}
            )
            await db.commit()
            return db_item
        except Exception:
            await db.rollback()
            raise
