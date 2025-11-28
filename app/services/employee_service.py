# app/services/employee_service.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, Employee
from app.schemas.dictionary import EmployeeCreate, EmployeeUpdate
from app.services.base_service import BaseService
from app.services.exceptions import DeletionError, DuplicateError


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

    async def create(
        self, db: AsyncSession, obj_in: EmployeeCreate, user_id: int
    ) -> Employee:
        # Уникальная логика: проверка дубликатов по двум полям
        if obj_in.employee_id:
            await self._check_duplicate(db, "employee_id", obj_in.employee_id)
        if obj_in.email:
            await self._check_duplicate(db, "email", obj_in.email)

        # Проверка уникальности ФИО

        await self._check_duplicate_name(
            db, obj_in.last_name, obj_in.first_name, obj_in.patronymic
        )

        return await super().create(db, obj_in, user_id)

    async def update(
        self, db: AsyncSession, obj_id: int, obj_in: EmployeeUpdate, user_id: int
    ) -> Employee | None:
        # Уникальная логика: проверка дубликатов по двум полям
        if obj_in.employee_id:
            await self._check_duplicate(
                db, "employee_id", obj_in.employee_id, current_id=obj_id
            )
        if obj_in.email:
            await self._check_duplicate(db, "email", obj_in.email, current_id=obj_id)

        # Проверка уникальности ФИО (если меняются поля имени)
        await self._check_duplicate_name(
            db,
            obj_in.last_name,
            obj_in.first_name,
            obj_in.patronymic,
            current_id=obj_id,
        )

        return await super().update(db, obj_id, obj_in, user_id)

    async def _check_duplicate_name(
        self,
        db: AsyncSession,
        last_name: str,
        first_name: str,
        patronymic: str | None,
        current_id: int | None = None,
    ):
        query = select(self.model.id).where(
            self.model.last_name == last_name,
            self.model.first_name == first_name,
            self.model.patronymic == patronymic,
        )
        if current_id:
            query = query.where(self.model.id != current_id)

        result = await db.execute(query.limit(1))
        if result.scalar_one_or_none() is not None:
            patr_str = f" {patronymic}" if patronymic else ""
            raise DuplicateError(
                f"Сотрудник с ФИО '{last_name} {first_name}{patr_str}' уже существует."
            )

    async def delete(
        self, db: AsyncSession, obj_id: int, user_id: int
    ) -> Employee | None:
        related_count = await self._count_related(db, Device.employee_id, obj_id)
        if related_count > 0:
            raise DeletionError(
                f"Невозможно удалить сотрудника, так как с ним связано {related_count} активов."
            )

        return await super().delete(db, obj_id, user_id)


# Создаем единственный экземпляр сервиса, передавая ему модель
employee_service = EmployeeService(Employee)
