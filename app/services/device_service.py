# app/services/device_service.py

import asyncio
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete, update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.asset import AssetUpdate, AssetCreate
from app.models import (
    Device, DeviceModel, AssetType, DeviceStatus, Department, Location, Employee, Manufacturer, Tag, Supplier
)
from .exceptions import DeviceNotFoundException, DuplicateDeviceError, NotFoundError
from app.services.audit_log_service import log_action

class DeviceService:
    """Сервис для бизнес-логики, связанной с активами/устройствами."""

    def __init__(self):
        # В будущем здесь могут быть зависимости, например, сервис логгирования
        pass

    # Методы чтения данных остаются почти без изменений,
    # но мы добавим загрузку тегов, чтобы они были доступны в ответах.
    async def get_device_with_relations(self, db: AsyncSession, device_id: int) -> Device | None:
        """Загружает актив со всеми связанными сущностями, включая теги."""
        stmt = select(Device).options(
            selectinload(Device.asset_type),
            selectinload(Device.device_model).selectinload(DeviceModel.manufacturer),
            selectinload(Device.status),
            selectinload(Device.department),
            selectinload(Device.location),
            selectinload(Device.employee),
            selectinload(Device.tags) #!# ДОБАВИЛИ ЗАГРУЗКУ ТЕГОВ
        ).where(Device.id == device_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_devices_with_filters(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        sort_by: str | None = None,
        sort_order: str = "asc", **filters
    ):
        """Получает устройства с фильтрацией, пагинацией и тегами."""
        query = select(Device).options(
            selectinload(Device.asset_type),
            selectinload(Device.device_model).options(
                selectinload(DeviceModel.manufacturer),
                selectinload(DeviceModel.asset_type)
            ),
            selectinload(Device.status),
            selectinload(Device.department),
            selectinload(Device.location),
            selectinload(Device.employee),
            # Загружаем теги для отображения в списке
            selectinload(Device.tags)
        )
        
        # Применение фильтров
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Device.inventory_number.ilike(search_term),
                    Device.serial_number.ilike(search_term),
                    Device.mac_address.ilike(search_term)
                )
            )
        
        if filters.get("asset_type_id"):
            query = query.filter(Device.asset_type_id == filters["asset_type_id"])
        if filters.get("status_id"):
            query = query.filter(Device.status_id == filters["status_id"])
        if filters.get("department_id"):
            query = query.filter(Device.department_id == filters["department_id"])
        if filters.get("location_id"):
            query = query.filter(Device.location_id == filters["location_id"])
        
        # Фильтр по производителю через связанную модель
        if filters.get("manufacturer_id"):
            query = query.join(Device.device_model).filter(DeviceModel.manufacturer_id == filters["manufacturer_id"])
            
        # Получение общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total_devices = (await db.execute(count_query)).scalar_one()

        # --- Сортировка ---
        sortable_columns = {
            "inventory_number": Device.inventory_number,
            "asset_type": AssetType.name,
            "device_model": DeviceModel.name,
            "status": DeviceStatus.name,
            "location": Location.name,
            "updated_at": Device.updated_at,
        }

        if sort_by and sort_by in sortable_columns:
            column_to_sort = sortable_columns[sort_by]
            
            # Для сортировки по связанным полям, нам нужен JOIN
            if sort_by == "asset_type":
                query = query.join(Device.asset_type, isouter=True)
            elif sort_by == "device_model":
                query = query.join(Device.device_model, isouter=True)
            elif sort_by == "status":
                query = query.join(Device.status, isouter=True)
            elif sort_by == "location":
                query = query.join(Device.location, isouter=True)

            query = query.order_by(column_to_sort.desc() if sort_order == "desc" else column_to_sort.asc())
        else:
            # Сортировка по умолчанию
            query = query.order_by(Device.id.desc())

        # Применение пагинации
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        paginated_devices = result.scalars().all()
        
        return paginated_devices, total_devices

    async def get_all_dictionaries_for_form(self, db: AsyncSession) -> dict:
        """Асинхронно загружает все справочники, необходимые для форм."""
        # !# ИСПРАВЛЕНИЕ: Выполняем запросы ПОСЛЕДОВАТЕЛЬНО, чтобы избежать конфликта сессий.
        # Это надежный и безопасный способ для работы с одной сессией.
        asset_types_res = await db.execute(select(AssetType).order_by(AssetType.name))
        device_models_res = await db.execute(select(DeviceModel).order_by(DeviceModel.name))
        device_statuses_res = await db.execute(select(DeviceStatus).order_by(DeviceStatus.name))
        departments_res = await db.execute(select(Department).order_by(Department.name))
        locations_res = await db.execute(select(Location).order_by(Location.name))
        employees_res = await db.execute(select(Employee).order_by(Employee.last_name))
        manufacturers_res = await db.execute(select(Manufacturer).order_by(Manufacturer.name))
        # Добавляем поставщиков, как и просили
        suppliers_res = await db.execute(select(Supplier).order_by(Supplier.name))
        
        return {
            "asset_types": asset_types_res.scalars().all(),
            "device_models": device_models_res.scalars().all(),
            "device_statuses": device_statuses_res.scalars().all(),
            "departments": departments_res.scalars().all(),
            "locations": locations_res.scalars().all(),
            "employees": employees_res.scalars().all(),
            "manufacturers": manufacturers_res.scalars().all(),
            "suppliers": suppliers_res.scalars().all(),
        }

    async def get_all_tags(self, db: AsyncSession) -> List[Tag]:
        """Возвращает список всех тегов, отсортированных по имени."""
        stmt = select(Tag).order_by(Tag.name)
        result = await db.execute(stmt)
        return result.scalars().all()



    async def update_device_with_audit(
        self,
        db: AsyncSession,
        device_id: int, update_data: AssetUpdate,
        user_id: int
    ) -> Device:
        """
        Обновляет актив, вычисляет изменения (включая теги) и логирует их.
        """
        db_device = await self.get_device_with_relations(db, device_id)
        if not db_device:
            raise DeviceNotFoundException(f"Устройство с id={device_id} не найдено.")

        # 1. Создаем Pydantic-схему из SQLAlchemy-объекта для получения "снимка" старых данных.
        old_data_schema = AssetUpdate.model_validate(db_device, from_attributes=True)
        # Добавляем ID текущих тегов в старую схему
        old_data_schema.tag_ids = [tag.id for tag in db_device.tags]
        
        # 2. Конвертируем старую и новую схемы в словари для сравнения. `exclude_unset=True` важен.
        old_data_dict = old_data_schema.model_dump()
        new_data_dict = update_data.model_dump(exclude_unset=True)

        # 3. Вычисляем разницу (diff) с помощью словарного включения.
        diff = {}
        for key, value in new_data_dict.items():
            # Сравниваем списки тегов отдельно
            if key == 'tag_ids':
                if sorted(old_data_dict.get(key, [])) != sorted(value or []):
                    diff[key] = {"old": old_data_dict.get(key, []), "new": value or []}
            elif old_data_dict.get(key) != value:
                diff[key] = {"old": old_data_dict.get(key), "new": value}

        if not diff:
            return db_device # Если изменений нет, ничего не делаем

        try:
            #!# 1. Работа с тегами (если они были переданы)
            if update_data.tag_ids is not None:
                # Находим новые объекты тегов
                new_tags = []
                if update_data.tag_ids:
                    tag_stmt = select(Tag).where(Tag.id.in_(update_data.tag_ids))
                    new_tags = (await db.execute(tag_stmt)).scalars().all()
                
                # Заменяем список тегов у объекта
                db_device.tags = new_tags

            # Обновляем остальные поля
            update_dict_simple_fields = {k: v for k, v in new_data_dict.items() if k != 'tag_ids'}
            for key, value in update_dict_simple_fields.items():
                setattr(db_device, key, value)
            
            db.add(db_device)

            # TODO: Добавить изменения тегов в details для log_action
            await log_action(
                db=db,
                user_id=user_id,
                action_type="update",
                entity_type="Device",
                entity_id=db_device.id,
                details={"changes": diff}
            )
            await db.commit()
            await db.refresh(db_device)
        except SQLAlchemyError as e:
            await db.rollback()
            raise e
        
        # Возвращаем обновленный объект со всеми связями
        return await self.get_device_with_relations(db, db_device.id)

    async def get_dashboard_stats(self, db: AsyncSession) -> dict:
        """Собирает статистику для дашборда."""
        try:
            # Общее количество активов
            total_devices_stmt = select(func.count(Device.id))

            # Статистика по типам устройств
            types_stmt = (
                select(AssetType.name, func.count(Device.id).label('count'))
                .outerjoin(Device, Device.asset_type_id == AssetType.id)
                .group_by(AssetType.id, AssetType.name).order_by(AssetType.name)
            )
            
            # Статистика по статусам устройств
            statuses_stmt = (
                select(DeviceStatus.name, func.count(Device.id).label('count'))
                .outerjoin(Device, Device.status_id == DeviceStatus.id)
                .group_by(DeviceStatus.id, DeviceStatus.name).order_by(DeviceStatus.name)
            )

            # Выполняем запросы параллельно и безопасно
            results = await asyncio.gather(
                db.execute(total_devices_stmt),
                db.execute(types_stmt),
                db.execute(statuses_stmt)
            )
            total_devices = results[0].scalar_one()
            device_types_list = [{'name': name, 'count': count} for name, count in results[1].all()]
            device_statuses_list = [{'name': name, 'count': count} for name, count in results[2].all()]
            
            return {
                "device_types_count": device_types_list,
                "device_statuses_count": device_statuses_list,
                "total_devices": total_devices,
            }
        except SQLAlchemyError as e:
            # Используем стандартный логгер вместо print
            logger.error(f"Database error in get_dashboard_stats: {e}", exc_info=True)
            raise e

    async def create_device(self, db: AsyncSession, asset_data: AssetCreate, user_id: int) -> Device:
        """Создает новый актив, проверяет на уникальность и логирует действие."""
        """
        Создает новый актив, генерирует инвентарный номер и связывает теги.
        """
        try:
            #!# 1. Генерация инвентарного номера (формат PREFIX-YYYYMMDD-NNN)
            # 1.1. Получаем префикс из связанного типа актива
            asset_type = await db.get(AssetType, asset_data.asset_type_id)
            if not asset_type:
                raise NotFoundError(f"Тип актива с id={asset_data.asset_type_id} не найден.")
            prefix = asset_type.prefix
            
            # 1.2. Формируем префикс для поиска за сегодняшний день
            date_str = datetime.utcnow().strftime('%Y%m%d')
            search_prefix = f"{prefix}-{date_str}-"
            
            # 1.3. Находим последний номер за сегодня
            last_device_stmt = select(Device.inventory_number).where(
                Device.inventory_number.like(f"{search_prefix}%")
            ).order_by(Device.inventory_number.desc()).limit(1)
            
            last_inv_number = (await db.execute(last_device_stmt)).scalar_one_or_none()
            
            # 1.4. Вычисляем следующий номер
            if last_inv_number:
                last_seq = int(last_inv_number.split('-')[-1])
                new_seq = last_seq + 1
            else:
                new_seq = 1
            
            # 1.5. Собираем финальный инвентарный номер
            inventory_number = f"{search_prefix}{new_seq:03d}"

            #!# 2. Работа с тегами
            tags = []
            if asset_data.tag_ids:
                tag_stmt = select(Tag).where(Tag.id.in_(asset_data.tag_ids))
                tags = (await db.execute(tag_stmt)).scalars().all()

            #!# 3. Создание объекта Device
            # Сначала берем данные из схемы
            device_dict = asset_data.model_dump(exclude={'tag_ids'})
            # Добавляем наш сгенерированный номер
            device_dict['inventory_number'] = inventory_number
            
            device = Device(**device_dict)
            # Присваиваем связанные объекты тегов
            device.tags = tags
            
            db.add(device)
            await db.flush()

            await log_action(
                db=db, user_id=user_id, action_type="create",
                entity_type="Device", entity_id=device.id,
                details={"inventory_number": device.inventory_number}
            )
            
            await db.commit()
            
        except SQLAlchemyError as e:
            await db.rollback()
            # Можно добавить логирование ошибки здесь
            raise e

        return await self.get_device_with_relations(db, device.id)

    async def bulk_delete_devices(self, db: AsyncSession, device_ids: list[int], user_id: int) -> tuple[int, list]:
        """
        Массово удаляет устройства по списку ID и логирует каждое действие.
        Всегда возвращает кортеж (deleted_count, errors).
        """
        errors = [] # Инициализируем пустой список для ошибок
        if not device_ids:
            return 0, errors # --- ИСПРАВЛЕНИЕ 1 ---

        # Для логирования нам нужно получить информацию об удаляемых объектах ДО их удаления
        stmt_select = select(Device).options(selectinload(Device.device_model)).where(Device.id.in_(device_ids))
        result = await db.execute(stmt_select)
        devices_to_delete = result.scalars().all()

        if not devices_to_delete:
            return 0, errors # --- ИСПРАВЛЕНИЕ 2 ---
        
        # Собираем реальные ID, которые будем удалять (на случай если какие-то не найдены)
        actual_device_ids = [d.id for d in devices_to_delete]

        try:
            # 1. Логируем каждое удаление
            for device in devices_to_delete:
                await log_action(
                    db=db, user_id=user_id, action_type="delete", entity_type="Device",
                    entity_id=device.id,
                    details={"inventory_number": device.inventory_number, "name": device.device_model.name if device.device_model else 'N/A'}
                )

            # 2. Выполняем массовое удаление
            stmt_delete = delete(Device).where(Device.id.in_(actual_device_ids))
            delete_result = await db.execute(stmt_delete)
            
            # 3. Коммитим транзакцию
            await db.commit()
            
            return delete_result.rowcount, errors # --- ИСПРАВЛЕНИЕ 3 ---
        except SQLAlchemyError as e:
            await db.rollback()
            # В случае ошибки возвращаем 0 удаленных и текст ошибки
            return 0, [str(e)] # --- ИСПРАВЛЕНИЕ 4 ---


    async def bulk_update_devices(self, db: AsyncSession, device_ids: list[int], update_data: dict, user_id: int) -> int:
        """
        Массово обновляет устройства, используя один UPDATE-запрос, и логирует каждое изменение.
        """
        if not device_ids or not update_data:
            return 0

        # 1. Получаем старые значения для логирования ДО обновления
        stmt_select = (
            select(Device)
            .options(
                selectinload(Device.status),
                selectinload(Device.department),
                selectinload(Device.location)
            )
            .where(Device.id.in_(device_ids))
        )
        old_devices = (await db.execute(stmt_select)).scalars().all()
        if not old_devices:
            return 0

        # 2. Асинхронно загружаем новые связанные объекты, только если они есть в update_data
        tasks = {
            "status": db.get(DeviceStatus, update_data["status_id"]) if "status_id" in update_data else None,
            "department": db.get(Department, update_data["department_id"]) if "department_id" in update_data else None,
            "location": db.get(Location, update_data["location_id"]) if "location_id" in update_data else None,
        }
        # Фильтруем None, чтобы не выполнять лишние await
        valid_tasks = {k: v for k, v in tasks.items() if v is not None}
        results = await asyncio.gather(*valid_tasks.values())
        new_related_models = dict(zip(valid_tasks.keys(), results))
        
        try:
            # 3. Генерируем diff и логируем для каждого устройства
            for device in old_devices:
                diff = {}
                if "status" in new_related_models and device.status_id != new_related_models["status"].id:
                    diff["Статус"] = {
                        "old": device.status.name if device.status else "",
                        "new": new_related_models["status"].name
                    }
                if "department" in new_related_models and device.department_id != new_related_models["department"].id:
                    diff["Отдел"] = {
                        "old": device.department.name if device.department else "",
                        "new": new_related_models["department"].name
                    }
                if "location" in new_related_models and device.location_id != new_related_models["location"].id:
                    diff["Местоположение"] = {
                        "old": device.location.name if device.location else "",
                        "new": new_related_models["location"].name
                    }

                # Если были изменения, логируем их
                if diff:
                    await log_action(
                        db=db, user_id=user_id, action_type="update", entity_type="Device",
                        entity_id=device.id, details={"diff": diff, "source": "bulk_update"},
                    )

            # 4. Выполняем массовое обновление одним запросом
            stmt_update = update(Device).where(Device.id.in_(device_ids)).values(**update_data)
            update_result = await db.execute(stmt_update)
            await db.commit()

            return update_result.rowcount
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def delete_device_with_audit(self, db: AsyncSession, device_id: int, user_id: int):
        """
        Удаляет одно устройство и логирует это действие в рамках одной транзакции.
        """
        stmt = select(Device).options(selectinload(Device.device_model)).where(Device.id == device_id)
        device = (await db.execute(stmt)).scalar_one_or_none()

        if not device:
            raise DeviceNotFoundException(f"Устройство с id={device_id} не найдено.")

        try:
            # 2. Добавляем запись в лог (в сессию)
            await log_action(
                db=db,
                user_id=user_id,
                action_type="delete",
                entity_type="Device",
                entity_id=device.id,
                details={"inventory_number": device.inventory_number, "name": device.device_model.name if device.device_model else 'N/A'}
            )

            # 3. Помечаем объект на удаление
            await db.delete(device)

            # 4. Коммитим транзакцию (удаление + лог)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise e