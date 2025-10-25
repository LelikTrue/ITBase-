# app/services/device_service.py

import asyncio
import logging
from datetime import date, datetime #!# Добавляем импорт date

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AssetType,
    Department,
    Device,
    DeviceModel,
    DeviceStatus,
    Employee,
    Location,
    Manufacturer,
    Supplier,
    Tag,
)
from app.schemas.asset import AssetCreate, AssetUpdate
from app.services.audit_log_service import log_action

from .exceptions import DeviceNotFoundException, NotFoundError

# Инициализация логгера для этого модуля
logger = logging.getLogger(__name__)


#!# ИЗМЕНЕНИЕ: Добавляем вспомогательную функцию для сериализации
def _serialize_value(value):
    """Преобразует значения, несовместимые с JSON, в строки."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class DeviceService:
    """Сервис для бизнес-логики, связанной с активами/устройствами."""

    def __init__(self):
        # В будущем здесь могут быть зависимости, например, сервис логгирования
        pass

    # Методы чтения данных остаются почти без изменений,
    async def get_device_with_relations(self, db: AsyncSession, device_id: int) -> Device | None:
        """Загружает актив со всеми связанными сущностями, включая теги."""
        stmt = select(Device).options(
            selectinload(Device.asset_type),
            selectinload(Device.device_model).selectinload(DeviceModel.manufacturer),
            selectinload(Device.status),
            selectinload(Device.department),
            selectinload(Device.location),
            selectinload(Device.employee),
            selectinload(Device.tags)
        ).where(Device.id == device_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_devices_with_filters(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        sort_by: str | None = None,
        sort_order: str = 'asc', **filters
    ):
        """ Получает устройства с фильтрацией, пагинацией и тегами."""
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
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    # !# ИЗМЕНЕНИЕ 1: Добавляем поиск по названию актива
                    Device.name.ilike(search_term),
                    Device.inventory_number.ilike(search_term),
                    Device.serial_number.ilike(search_term),
                    Device.mac_address.ilike(search_term)
                )
            )

        if filters.get('asset_type_id'):
            query = query.filter(Device.asset_type_id == filters['asset_type_id'])
        if filters.get('status_id'):
            query = query.filter(Device.status_id == filters['status_id'])
        if filters.get('department_id'):
            query = query.filter(Device.department_id == filters['department_id'])
        if filters.get('location_id'):
            query = query.filter(Device.location_id == filters['location_id'])

        # Фильтр по производителю через связанную модель
        if filters.get('manufacturer_id'):
            query = query.join(Device.device_model).filter(DeviceModel.manufacturer_id == filters['manufacturer_id'])

        # Получение общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total_devices = (await db.execute(count_query)).scalar_one()

        # --- Сортировка ---
        sortable_columns = {
            # !# ИЗМЕНЕНИЕ 2: Добавляем сортировку по названию актива
            'name': Device.name,
            'inventory_number': Device.inventory_number,
            'asset_type': AssetType.name,
            'device_model': DeviceModel.name,
            'status': DeviceStatus.name,
            'location': Location.name,
            'updated_at': Device.updated_at,
        }

        if sort_by and sort_by in sortable_columns:
            column_to_sort = sortable_columns[sort_by]

            # Для сортировки по связанным полям, нам нужен JOIN
            if sort_by == 'asset_type':
                query = query.join(Device.asset_type, isouter=True)
            elif sort_by == 'device_model':
                query = query.join(Device.device_model, isouter=True)
            elif sort_by == 'status':
                query = query.join(Device.status, isouter=True)
            elif sort_by == 'location':
                query = query.join(Device.location, isouter=True)

            query = query.order_by(column_to_sort.desc() if sort_order == 'desc' else column_to_sort.asc())
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
        asset_types_res = await db.execute(select(AssetType).order_by(AssetType.name))
        device_models_res = await db.execute(select(DeviceModel).order_by(DeviceModel.name))
        device_statuses_res = await db.execute(select(DeviceStatus).order_by(DeviceStatus.name))
        departments_res = await db.execute(select(Department).order_by(Department.name))
        locations_res = await db.execute(select(Location).order_by(Location.name))
        employees_res = await db.execute(select(Employee).order_by(Employee.last_name))
        manufacturers_res = await db.execute(select(Manufacturer).order_by(Manufacturer.name))
        suppliers_res = await db.execute(select(Supplier).order_by(Supplier.name))

        return {
            'asset_types': asset_types_res.scalars().all(),
            'device_models': device_models_res.scalars().all(),
            'device_statuses': device_statuses_res.scalars().all(),
            'departments': departments_res.scalars().all(),
            'locations': locations_res.scalars().all(),
            'employees': employees_res.scalars().all(),
            'manufacturers': manufacturers_res.scalars().all(),
            'suppliers': suppliers_res.scalars().all(),
        }

    async def get_all_tags(self, db: AsyncSession) -> list[Tag]:
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
            raise DeviceNotFoundException(f'Устройство с id={device_id} не найдено.')

        old_data_schema = AssetUpdate.model_validate(db_device, from_attributes=True)
        old_data_schema.tag_ids = [tag.id for tag in db_device.tags]

        old_data_dict = old_data_schema.model_dump()
        new_data_dict = update_data.model_dump(exclude_unset=True)

        #!# ИЗМЕНЕНИЕ: Улучшенная и исправленная логика создания diff
        diff = {}
        for key, new_value in new_data_dict.items():
            old_value = old_data_dict.get(key)

            # 1. Сначала обрабатываем особый случай с тегами (сравнение списков)
            if key == 'tag_ids':
                # Приводим к множествам для корректного сравнения неупорядоченных id
                if set(old_value or []) != set(new_value or []):
                    diff[key] = {
                        'old': old_value or [],
                        'new': new_value or []
                    }
            # 2. Затем обрабатываем все остальные поля
            elif old_value != new_value:
                # Сравниваем напрямую. Python умеет сравнивать даты, строки, числа.
                # Только после того, как нашли различие, сериализуем значения для лога.
                diff[key] = {
                    'old': _serialize_value(old_value),
                    'new': _serialize_value(new_value)
                }

        if not diff:
            return db_device # Если изменений нет, ничего не делаем

        try:
            if update_data.tag_ids is not None:
                new_tags = []
                if update_data.tag_ids:
                    tag_stmt = select(Tag).where(Tag.id.in_(update_data.tag_ids))
                    new_tags = (await db.execute(tag_stmt)).scalars().all()
                db_device.tags = new_tags

            update_dict_simple_fields = {k: v for k, v in new_data_dict.items() if k != 'tag_ids'}
            for key, value in update_dict_simple_fields.items():
                setattr(db_device, key, value)

            db.add(db_device)

            await log_action(
                db=db,
                user_id=user_id,
                action_type='update',
                entity_type='Device',
                entity_id=db_device.id,
                details={'changes': diff}
            )
            await db.commit()
            await db.refresh(db_device)
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

        return await self.get_device_with_relations(db, db_device.id)

    async def get_dashboard_stats(self, db: AsyncSession) -> dict:
        """Собирает статистику для дашборда."""
        try:
            total_devices_stmt = select(func.count(Device.id))
            types_stmt = (
                select(AssetType.name, func.count(Device.id).label('count'))
                .outerjoin(Device, Device.asset_type_id == AssetType.id)
                .group_by(AssetType.id, AssetType.name).order_by(AssetType.name)
            )
            statuses_stmt = (
                select(DeviceStatus.name, func.count(Device.id).label('count'))
                .outerjoin(Device, Device.status_id == DeviceStatus.id)
                .group_by(DeviceStatus.id, DeviceStatus.name).order_by(DeviceStatus.name)
            )

            total_devices_res = await db.execute(total_devices_stmt)
            types_res = await db.execute(types_stmt)
            statuses_res = await db.execute(statuses_stmt)

            total_devices = total_devices_res.scalar_one()
            device_types_list = [{'name': name, 'count': count} for name, count in types_res.all()]
            device_statuses_list = [{'name': name, 'count': count} for name, count in statuses_res.all()]

            return {
                'device_types_count': device_types_list,
                'device_statuses_count': device_statuses_list,
                'total_devices': total_devices,
            }
        except SQLAlchemyError as e:
            logger.error(f'Database error in get_dashboard_stats: {e}', exc_info=True)
            raise e

    async def create_device(self, db: AsyncSession, asset_data: AssetCreate, user_id: int) -> Device:
        """Создает новый актив, генерирует инвентарный номер и связывает теги."""
        try:
            asset_type = await db.get(AssetType, asset_data.asset_type_id)
            if not asset_type:
                raise NotFoundError(f'Тип актива с id={asset_data.asset_type_id} не найден.')
            prefix = asset_type.prefix

            date_str = datetime.utcnow().strftime('%Y%m%d')
            search_prefix = f'{prefix}-{date_str}-'

            last_device_stmt = select(Device.inventory_number).where(
                Device.inventory_number.like(f'{search_prefix}%')
            ).order_by(Device.inventory_number.desc()).limit(1)

            last_inv_number = (await db.execute(last_device_stmt)).scalar_one_or_none()

            if last_inv_number:
                last_seq = int(last_inv_number.split('-')[-1])
                new_seq = last_seq + 1
            else:
                new_seq = 1

            inventory_number = f'{search_prefix}{new_seq:03d}'

            tags = []
            if asset_data.tag_ids:
                tag_stmt = select(Tag).where(Tag.id.in_(asset_data.tag_ids))
                tags = (await db.execute(tag_stmt)).scalars().all()

            device_dict = asset_data.model_dump(exclude={'tag_ids'})
            device_dict['inventory_number'] = inventory_number

            device = Device(**device_dict)
            device.tags = tags

            db.add(device)
            await db.flush()

            await log_action(
                db=db, user_id=user_id, action_type='create',
                entity_type='Device', entity_id=device.id,
                # !# ИЗМЕНЕНИЕ 3: Добавляем name в лог создания
                details={'inventory_number': device.inventory_number, 'name': device.name}
            )

            await db.commit()

        except SQLAlchemyError as e:
            await db.rollback()
            raise e

        return await self.get_device_with_relations(db, device.id)

    async def bulk_delete_devices(self, db: AsyncSession, device_ids: list[int], user_id: int) -> tuple[int, list]:
        """
        Массово удаляет устройства по списку ID и логирует каждое действие.
        Всегда возвращает кортеж (deleted_count, errors).
        """
        errors = []
        if not device_ids:
            return 0, errors

        stmt_select = select(Device).options(selectinload(Device.device_model)).where(Device.id.in_(device_ids))
        result = await db.execute(stmt_select)
        devices_to_delete = result.scalars().all()

        if not devices_to_delete:
            return 0, errors

        actual_device_ids = [d.id for d in devices_to_delete]

        try:
            for device in devices_to_delete:
                await log_action(
                    db=db, user_id=user_id, action_type='delete', entity_type='Device',
                    entity_id=device.id,
                # !# ИЗМЕНЕНИЕ 4: Исправляем логирование, добавляем device.name
                details={'inventory_number': device.inventory_number, 'name': device.name}
                )

            stmt_delete = delete(Device).where(Device.id.in_(actual_device_ids))
            delete_result = await db.execute(stmt_delete)

            await db.commit()

            return delete_result.rowcount, errors
        except SQLAlchemyError as e:
            await db.rollback()
            return 0, [str(e)]


    async def bulk_update_devices(self, db: AsyncSession, device_ids: list[int], update_data: dict, user_id: int) -> int:
        """
        Массово обновляет устройства, используя один UPDATE-запрос, и логирует каждое изменение.
        """
        if not device_ids or not update_data:
            return 0

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

        tasks = {
            'status': db.get(DeviceStatus, update_data['status_id']) if 'status_id' in update_data else None,
            'department': db.get(Department, update_data['department_id']) if 'department_id' in update_data else None,
            'location': db.get(Location, update_data['location_id']) if 'location_id' in update_data else None,
        }
        valid_tasks = {k: v for k, v in tasks.items() if v is not None}
        results = await asyncio.gather(*valid_tasks.values())
        new_related_models = dict(zip(valid_tasks.keys(), results, strict=False))

        try:
            for device in old_devices:
                diff = {}
                if 'status' in new_related_models and device.status_id != new_related_models['status'].id:
                    diff['Статус'] = {
                        'old': device.status.name if device.status else '',
                        'new': new_related_models['status'].name
                    }
                if 'department' in new_related_models and device.department_id != new_related_models['department'].id:
                    diff['Отдел'] = {
                        'old': device.department.name if device.department else '',
                        'new': new_related_models['department'].name
                    }
                if 'location' in new_related_models and device.location_id != new_related_models['location'].id:
                    diff['Местоположение'] = {
                        'old': device.location.name if device.location else '',
                        'new': new_related_models['location'].name
                    }

                if diff:
                    await log_action(
                        db=db, user_id=user_id, action_type='update', entity_type='Device',
                        entity_id=device.id, details={'diff': diff, 'source': 'bulk_update'},
                    )

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
            raise DeviceNotFoundException(f'Устройство с id={device_id} не найдено.')

        try:
            await log_action(
                db=db,
                user_id=user_id,
                action_type='delete',
                entity_type='Device',
                entity_id=device.id,
                # !# ИЗМЕНЕНИЕ 5: Исправляем логирование и здесь
                details={'inventory_number': device.inventory_number, 'name': device.name}
            )

            await db.delete(device)

            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise e