# app/services/dictionary_service.py
import logging
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select

# --- ИЗМЕНЕНИЕ 1: Импортируем IntegrityError ---
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Base
from app.schemas.dictionary import (
    AssetTypeCreate,
    DepartmentCreate,
    DeviceModelCreate,
    DeviceStatusCreate,
    EmployeeCreate,
    LocationCreate,
    ManufacturerCreate,
    SupplierCreate,
)

# --- ИЗМЕНЕНИЕ 2: Импортируем наше кастомное исключение ---
from app.services.exceptions import DuplicateError

logger = logging.getLogger(__name__)


class DictionaryService:
    """Сервис для управления операциями со справочниками."""

    async def _create_item(
        self, db: AsyncSession, model: type[Base], data: BaseModel
    ) -> Base:
        """Универсальный метод для создания записи в справочнике."""
        try:
            db_item = model(**data.model_dump())
            db.add(db_item)
            await db.commit()
            await db.refresh(db_item)
            return db_item
        # --- ИЗМЕНЕНИЕ 3: Добавляем обработку конкретной ошибки уникальности ---
        except IntegrityError as e:
            await db.rollback()
            logger.warning(
                f"Ошибка уникальности при создании записи в {model.__name__}: {e}"
            )
            # Превращаем ошибку БД в наше исключение бизнес-логики
            raise DuplicateError("Запись с таким названием уже существует.")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(
                f"Ошибка базы данных при создании записи в {model.__name__}: {e}",
                exc_info=True,
            )
            # Пробрасываем остальные ошибки БД как есть
            raise

    async def get_all(self, db: AsyncSession, model: type[Base]) -> list[Any]:
        """Получает все записи из указанной таблицы-справочника."""
        stmt = select(model).order_by(getattr(model, "name", model.id))
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_asset_type(self, db: AsyncSession, data: AssetTypeCreate) -> Base:
        from app.models import AssetType

        return await self._create_item(db, AssetType, data)

    async def create_device_model(
        self, db: AsyncSession, data: DeviceModelCreate
    ) -> Base:
        from app.models import DeviceModel

        return await self._create_item(db, DeviceModel, data)

    async def create_device_status(
        self, db: AsyncSession, data: DeviceStatusCreate
    ) -> Base:
        from app.models import DeviceStatus

        return await self._create_item(db, DeviceStatus, data)

    async def create_manufacturer(
        self, db: AsyncSession, data: ManufacturerCreate
    ) -> Base:
        from app.models import Manufacturer

        return await self._create_item(db, Manufacturer, data)

    async def create_department(self, db: AsyncSession, data: DepartmentCreate) -> Base:
        from app.models import Department

        return await self._create_item(db, Department, data)

    async def create_location(self, db: AsyncSession, data: LocationCreate) -> Base:
        from app.models import Location

        return await self._create_item(db, Location, data)

    async def create_employee(self, db: AsyncSession, data: EmployeeCreate) -> Base:
        from app.models import Employee

        return await self._create_item(db, Employee, data)

    async def create_supplier(self, db: AsyncSession, data: SupplierCreate) -> Base:
        from app.models import Supplier

        return await self._create_item(db, Supplier, data)
