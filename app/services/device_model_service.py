# app/services/device_model_service.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AssetType, Device, DeviceModel, Manufacturer
from app.schemas.dictionary import DeviceModelCreate, DeviceModelUpdate
from app.services.base_service import BaseService
from app.services.exceptions import DeletionError, DuplicateError, NotFoundError


class DeviceModelService(
    BaseService[DeviceModel, DeviceModelCreate, DeviceModelUpdate]
):
    """
    Сервис для управления моделями устройств.
    Имеет сложную бизнес-логику:
    - Проверка уникальности по паре (name, manufacturer_id).
    - Проверка существования связанных Manufacturer и AssetType.
    - Загрузка связанных данных в get_all().
    """

    async def get_all(self, db: AsyncSession) -> list[DeviceModel]:
        """Переопределяем get_all для загрузки связанных сущностей."""
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.manufacturer),
                selectinload(self.model.asset_type),
            )
            .order_by(self.model.name)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def _check_related_entities_exist(
        self, db: AsyncSession, manufacturer_id: int, asset_type_id: int
    ):
        """Проверяет, что производитель и тип актива существуют."""
        if not await db.get(Manufacturer, manufacturer_id):
            raise NotFoundError(f'Производитель с ID {manufacturer_id} не найден.')
        if not await db.get(AssetType, asset_type_id):
            raise NotFoundError(f'Тип актива с ID {asset_type_id} не найден.')

    async def _check_composite_duplicate(
        self,
        db: AsyncSession,
        name: str,
        manufacturer_id: int,
        current_id: int | None = None,
    ):
        """Проверяет уникальность по паре (name, manufacturer_id)."""
        query = select(self.model.id).where(
            self.model.name == name, self.model.manufacturer_id == manufacturer_id
        )
        if current_id:
            query = query.where(self.model.id != current_id)

        result = await db.execute(query.limit(1))
        if result.scalar_one_or_none() is not None:
            raise DuplicateError(
                f"Модель '{name}' для данного производителя уже существует."
            )

    async def create(
        self, db: AsyncSession, obj_in: DeviceModelCreate, user_id: int
    ) -> DeviceModel:
        await self._check_related_entities_exist(
            db, obj_in.manufacturer_id, obj_in.asset_type_id
        )
        await self._check_composite_duplicate(db, obj_in.name, obj_in.manufacturer_id)
        return await super().create(db, obj_in, user_id)

    async def update(
        self, db: AsyncSession, obj_id: int, obj_in: DeviceModelUpdate, user_id: int
    ) -> DeviceModel | None:
        # Pydantic схемы гарантируют наличие всех полей
        await self._check_related_entities_exist(
            db, obj_in.manufacturer_id, obj_in.asset_type_id
        )
        await self._check_composite_duplicate(
            db, obj_in.name, obj_in.manufacturer_id, current_id=obj_id
        )
        return await super().update(db, obj_id, obj_in, user_id)

    async def delete(
        self, db: AsyncSession, obj_id: int, user_id: int
    ) -> DeviceModel | None:
        related_count = await self._count_related(db, Device.device_model_id, obj_id)
        if related_count > 0:
            raise DeletionError(
                f'Невозможно удалить модель, так как с ней связано {related_count} активов.'
            )
        return await super().delete(db, obj_id, user_id)


# Создаем единственный экземпляр сервиса, передавая ему модель
device_model_service = DeviceModelService(DeviceModel)
