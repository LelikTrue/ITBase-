import yaml
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.asset_type import AssetType
from app.models.device_status import DeviceStatus
from app.models.department import Department
from app.models.location import Location
from app.schemas.initial_data import InitialDataSchema

logger = logging.getLogger(__name__)


class InitialDataService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_from_yaml(self, file_path: str = "initial_data.yaml") -> None:
        """
        Читает YAML файл и синхронизирует справочники.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"File {file_path} not found.")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            raise

        # Валидация через Pydantic
        try:
            data = InitialDataSchema(**raw_data)
        except Exception as e:
            logger.error(f"Validation error in initial_data.yaml: {e}")
            raise

        # Синхронизация каждой таблицы
        await self._sync_table(AssetType, data.asset_types)
        await self._sync_table(DeviceStatus, data.device_statuses)
        await self._sync_table(Department, data.departments)
        await self._sync_table(Location, data.locations)

        await self.db.commit()
        logger.info("Initial data seeding completed successfully.")

    async def _sync_table(self, model_class, items: list):
        """
        Generic метод для синхронизации.
        Ищет по slug. Если находит - обновляет name. Если нет - создает.
        """
        for item in items:
            # 1. Поиск: ищем по slug (основной ключ) или по name (чтобы избежать дублей)
            stmt = select(model_class).where(
                or_(model_class.slug == item.slug, model_class.name == item.name)
            )
            result = await self.db.execute(stmt)
            obj = result.scalars().first()

            if obj:
                # 2. UPDATE: Обновляем запись, если нашли совпадение по slug или name
                updates = []
                
                # Если нашли по имени, но slug пустой или другой - обновляем slug
                if obj.slug != item.slug:
                    logger.info(f"Updating slug for {model_class.__tablename__}: {obj.name} -> {item.slug}")
                    obj.slug = item.slug
                    updates.append("slug")

                if obj.name != item.name:
                    logger.info(f"Updating name for {model_class.__tablename__}: {obj.slug} -> {item.name}")
                    obj.name = item.name
                    updates.append("name")

                if hasattr(obj, 'description') and item.description:
                    if obj.description != item.description:
                        obj.description = item.description
                        updates.append("description")

                if hasattr(obj, 'prefix') and item.prefix:
                    if obj.prefix != item.prefix:
                        obj.prefix = item.prefix
                        updates.append("prefix")
                
                if updates:
                    logger.info(f"Updated fields for {item.slug}: {updates}")
            else:
                # 3. INSERT: Создаем новую запись
                logger.info(f"Creating {model_class.__tablename__}: {item.slug}")
                data_dict = item.model_dump(exclude_unset=True)
                new_obj = model_class(**data_dict)
                self.db.add(new_obj)
