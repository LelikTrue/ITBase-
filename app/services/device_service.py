import asyncio
import json
import logging
from datetime import date, datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_polymorphic

from app.models import (
    AssetType,
    Component,
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
from app.models.component import (
    ComponentCPU,
    ComponentGPU,
    ComponentMotherboard,
    ComponentRAM,
    ComponentStorage,
)
from app.schemas.asset import AssetCreate, AssetUpdate
from app.schemas.component import ComponentUploadRequest
from app.services.audit_log_service import log_action
from app.services.component_service import ComponentService

from .exceptions import DeviceNotFoundException, DuplicateDeviceError, NotFoundError

logger = logging.getLogger(__name__)


def _serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class DeviceService:
    def __init__(self):
        pass

    async def create_from_agent_data(self, file: UploadFile, session: AsyncSession, user_id: int) -> Device:
        """
        Создает актив на основе JSON-отчета агента.
        Автоматически создает/находит производителя и модель по материнской плате.
        """
        # 1. Парсинг и валидация JSON
        dto = await self._parse_agent_data(file)
        hostname = dto.hostname

        # 2. Извлечение ключевых данных
        mb_info, mb_manufacturer, mb_product = self._extract_mb_info(dto.components)

        # 3. Работа со справочниками (Get or Create)
        manufacturer = await self._get_or_create_manufacturer(session, mb_manufacturer)
        asset_type = await self._get_or_create_asset_type(session)
        device_model = await self._get_or_create_device_model(
            session, mb_product, manufacturer.id, asset_type.id
        )
        status = await self._get_default_status(session)

        # 4. Создание Устройства
        inventory_number = await self._generate_inventory_number(
            session, asset_type.prefix or "DEV"
        )

        new_device = Device(
            name=hostname,
            inventory_number=inventory_number,
            serial_number=mb_info.serial_number if mb_info else None,
            asset_type_id=asset_type.id,
            device_model_id=device_model.id,
            status_id=status.id,
            location_id=None,
            notes="Автоматически импортировано из агента",
        )

        await self._save_new_device(session, new_device)

        # Логируем создание
        await log_action(
            db=session,
            user_id=user_id,
            action_type="create",
            entity_type="Device",
            entity_id=new_device.id,
            details={
                "inventory_number": new_device.inventory_number,
                "name": new_device.name,
                "source": "agent_import",
            },
        )

        # 5. Синхронизация компонентов
        await ComponentService.sync_components(session, new_device.id, dto.components)

        return new_device

    async def _parse_agent_data(self, file: UploadFile) -> ComponentUploadRequest:
        content = await file.read()
        try:
            raw_data = json.loads(content)
            if isinstance(raw_data, list):
                # Fallback: try to find hostname in components or use default
                return ComponentUploadRequest(hostname="Imported-Host", components=raw_data)
            return ComponentUploadRequest(**raw_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e!s}")

    def _extract_mb_info(self, components):
        mb_info = next((c for c in components if c.type == "motherboard"), None)
        mb_manufacturer = mb_info.manufacturer if mb_info and mb_info.manufacturer else "Unknown"
        mb_product = mb_info.name if mb_info and mb_info.name else "Generic PC"
        return mb_info, mb_manufacturer, mb_product

    async def _get_or_create_manufacturer(self, session: AsyncSession, name: str) -> Manufacturer:
        stmt = select(Manufacturer).where(Manufacturer.name == name)
        m_result = await session.execute(stmt)
        manufacturer = m_result.scalars().first()
        if not manufacturer:
            manufacturer = Manufacturer(name=name)
            session.add(manufacturer)
            await session.flush()
        return manufacturer

    async def _get_or_create_asset_type(
        self, session: AsyncSession, name: str = "Системный блок", prefix: str = "PC"
    ) -> AssetType:
        stmt = select(AssetType).where(or_(AssetType.name == name, AssetType.prefix == prefix))
        t_result = await session.execute(stmt)
        candidates = t_result.scalars().all()

        # Приоритет 1: Сопадение по имени
        asset_type = next((x for x in candidates if x.name == name), None)
        # Приоритет 2: Сопадение по префиксу
        if not asset_type:
            asset_type = next((x for x in candidates if x.prefix == prefix), None)

        if not asset_type:
            asset_type = AssetType(name=name, prefix=prefix)
            session.add(asset_type)
            await session.flush()
        return asset_type

    async def _get_or_create_device_model(
        self, session: AsyncSession, name: str, manufacturer_id: int, asset_type_id: int
    ) -> DeviceModel:
        stmt = select(DeviceModel).where(
            DeviceModel.name == name, DeviceModel.manufacturer_id == manufacturer_id
        )
        dm_result = await session.execute(stmt)
        device_model = dm_result.scalars().first()
        if not device_model:
            device_model = DeviceModel(
                name=name, manufacturer_id=manufacturer_id, asset_type_id=asset_type_id
            )
            session.add(device_model)
            await session.flush()
        return device_model

    async def _get_default_status(self, session: AsyncSession) -> DeviceStatus:
        stmt = select(DeviceStatus).where(DeviceStatus.name == "На складе")
        s_result = await session.execute(stmt)
        status = s_result.scalars().first()

        if not status:
            stmt = select(DeviceStatus).limit(1)
            s_result = await session.execute(stmt)
            status = s_result.scalars().first()

        if not status:
            raise HTTPException(
                status_code=500, detail="No Device Statuses found in DB. Please create at least one status."
            )
        return status

    async def _generate_inventory_number(self, session: AsyncSession, prefix: str) -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        search_prefix = f"{prefix}-{date_str}-"
        last_device_stmt = (
            select(Device.inventory_number)
            .where(Device.inventory_number.like(f"{search_prefix}%"))
            .order_by(Device.inventory_number.desc())
            .limit(1)
        )
        last_inv_number = (await session.execute(last_device_stmt)).scalar_one_or_none()
        new_seq = int(last_inv_number.split("-")[-1]) + 1 if last_inv_number else 1
        return f"{search_prefix}{new_seq:03d}"

    async def _save_new_device(self, session: AsyncSession, new_device: Device):
        try:
            session.add(new_device)
            await session.flush()
        except IntegrityError as e:
            await session.rollback()
            error_info = str(e.orig) if hasattr(e, 'orig') else str(e)
            if 'serial_number' in error_info:
                raise HTTPException(
                    status_code=409,
                    detail=f"Актив с серийным номером '{new_device.serial_number}' уже существует."
                )
            elif 'inventory_number' in error_info:
                raise HTTPException(
                    status_code=409,
                    detail=f"Актив с инвентарным номером '{new_device.inventory_number}' уже существует."
                )
            else:
                raise HTTPException(status_code=409, detail="Актив с такими данными уже существует.")

    async def get_device_with_relations(self, db: AsyncSession, device_id: int) -> Device | None:
        # Создаем полиморфную сущность для загрузки всех типов компонентов
        poly_component = with_polymorphic(
            Component, [ComponentCPU, ComponentRAM, ComponentStorage, ComponentGPU, ComponentMotherboard]
        )

        stmt = (
            select(Device)
            .options(
                selectinload(Device.asset_type),
                selectinload(Device.device_model).selectinload(DeviceModel.manufacturer),
                selectinload(Device.status),
                selectinload(Device.department),
                selectinload(Device.location),
                selectinload(Device.employee),
                selectinload(Device.tags),
                selectinload(Device.supplier),
                selectinload(Device.components.of_type(poly_component)),  # Polymorphic eager load
                selectinload(Device.component_history),  # Eager load history
            )
            .where(Device.id == device_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    def _apply_filters(self, query, filters):
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Device.name.ilike(search_term),
                    Device.inventory_number.ilike(search_term),
                    Device.serial_number.ilike(search_term),
                    Device.mac_address.ilike(search_term),
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
        if filters.get("manufacturer_id"):
            query = query.join(Device.device_model).filter(DeviceModel.manufacturer_id == filters["manufacturer_id"])

        return query

    def _apply_sorting(self, query, sort_by, sort_order):
        sortable_columns = {
            "name": Device.name,
            "inventory_number": Device.inventory_number,
            "asset_type": AssetType.name,
            "device_model": DeviceModel.name,
            "status": DeviceStatus.name,
            "location": Location.name,
            "updated_at": Device.updated_at,
            "tags": func.min(Tag.name),
        }

        if sort_by and sort_by in sortable_columns:
            column_to_sort = sortable_columns[sort_by]
            if sort_by == "asset_type":
                query = query.join(Device.asset_type, isouter=True)
            elif sort_by == "device_model":
                query = query.join(Device.device_model, isouter=True)
            elif sort_by == "status":
                query = query.join(Device.status, isouter=True)
            elif sort_by == "location":
                query = query.join(Device.location, isouter=True)
            elif sort_by == "tags":
                query = query.outerjoin(Device.tags).group_by(Device.id)

            query = query.order_by(column_to_sort.desc() if sort_order == "desc" else column_to_sort.asc())
        else:
            query = query.order_by(Device.id.desc())

        return query

    async def get_devices_with_filters(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        sort_by: str | None = None,
        sort_order: str = "asc",
        **filters,
    ):
        query = select(Device).options(
            selectinload(Device.asset_type),
            selectinload(Device.device_model).options(
                selectinload(DeviceModel.manufacturer),
                selectinload(DeviceModel.asset_type),
            ),
            selectinload(Device.status),
            selectinload(Device.department),
            selectinload(Device.location),
            selectinload(Device.employee),
            selectinload(Device.tags),
            selectinload(Device.supplier),
        )

        query = self._apply_filters(query, filters)

        count_query = select(func.count()).select_from(query.subquery())
        total_devices = (await db.execute(count_query)).scalar_one()

        query = self._apply_sorting(query, sort_by, sort_order)

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        paginated_devices = result.scalars().all()
        return paginated_devices, total_devices

    async def get_all_dictionaries_for_form(self, db: AsyncSession) -> dict:
        asset_types_res = await db.execute(select(AssetType).order_by(AssetType.name))
        device_models_res = await db.execute(select(DeviceModel).order_by(DeviceModel.name))
        device_statuses_res = await db.execute(select(DeviceStatus).order_by(DeviceStatus.name))
        departments_res = await db.execute(select(Department).order_by(Department.name))
        locations_res = await db.execute(select(Location).order_by(Location.name))
        employees_res = await db.execute(select(Employee).order_by(Employee.last_name))
        manufacturers_res = await db.execute(select(Manufacturer).order_by(Manufacturer.name))
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

    # ... остальные методы без изменений ...
    async def get_all_tags(self, db: AsyncSession) -> list[Tag]:
        stmt = select(Tag).order_by(Tag.name)
        result = await db.execute(stmt)
        return result.scalars().all()

    def _calculate_device_diff(self, db_device: Device, update_data: AssetUpdate) -> dict:
        old_data_schema = AssetUpdate.model_validate(db_device, from_attributes=True)
        old_data_schema.tag_ids = [tag.id for tag in db_device.tags]

        old_data_dict = old_data_schema.model_dump()
        new_data_dict = update_data.model_dump(exclude_unset=True)

        diff = {}
        for key, new_value in new_data_dict.items():
            old_value = old_data_dict.get(key)
            if key == "tag_ids":
                if set(old_value or []) != set(new_value or []):
                    diff[key] = {"old": old_value or [], "new": new_value or []}
            elif old_value != new_value:
                diff[key] = {
                    "old": _serialize_value(old_value),
                    "new": _serialize_value(new_value),
                }
        return diff

    async def _update_tags_if_needed(self, db: AsyncSession, db_device: Device, update_data: AssetUpdate):
        if update_data.tag_ids is not None:
            new_tags = []
            if update_data.tag_ids:
                tag_stmt = select(Tag).where(Tag.id.in_(update_data.tag_ids))
                new_tags = (await db.execute(tag_stmt)).scalars().all()
            db_device.tags = new_tags

    def _apply_simple_updates(self, db_device: Device, update_data: AssetUpdate):
        new_data_dict = update_data.model_dump(exclude_unset=True)
        update_dict_simple_fields = {
            k: v for k, v in new_data_dict.items() if k not in ("tag_ids", "manufacturer_id")
        }
        for key, value in update_dict_simple_fields.items():
            setattr(db_device, key, value)

    async def update_device_with_audit(
        self, db: AsyncSession, device_id: int, update_data: AssetUpdate, user_id: int
    ) -> Device:
        db_device = await self.get_device_with_relations(db, device_id)
        if not db_device:
            raise DeviceNotFoundException(f"Устройство с id={device_id} не найдено.")

        diff = self._calculate_device_diff(db_device, update_data)
        if not diff:
            return db_device

        try:
            await self._update_tags_if_needed(db, db_device, update_data)
            self._apply_simple_updates(db_device, update_data)

            db.add(db_device)
            await log_action(
                db=db,
                user_id=user_id,
                action_type="update",
                entity_type="Device",
                entity_id=db_device.id,
                details={"changes": diff},
            )
            await db.commit()
            await db.refresh(db_device)
        except IntegrityError as e:
            await db.rollback()
            error_info = str(e.orig) if hasattr(e, 'orig') else str(e)
            # Парсим понятное сообщение
            if 'serial_number' in error_info:
                raise DuplicateDeviceError(
                    f"Актив с серийным номером '{update_data.serial_number}' уже существует."
                )
            elif 'mac_address' in error_info:
                raise DuplicateDeviceError(
                    f"Актив с MAC-адресом '{update_data.mac_address}' уже существует."
                )
            elif 'inventory_number' in error_info:
                raise DuplicateDeviceError(
                    f"Актив с инвентарным номером '{update_data.inventory_number}' уже существует."
                )
            else:
                raise DuplicateDeviceError("Актив с такими данными уже существует.")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Ошибка при обновлении устройства ID {device_id}: {e}", exc_info=True)
            raise e

        return await self.get_device_with_relations(db, db_device.id)

    async def get_dashboard_stats(self, db: AsyncSession) -> dict:
        try:
            total_devices_stmt = select(func.count(Device.id))
            types_stmt = (
                select(AssetType.name, func.count(Device.id).label("count"))
                .outerjoin(Device, Device.asset_type_id == AssetType.id)
                .group_by(AssetType.id, AssetType.name)
                .order_by(AssetType.name)
            )
            statuses_stmt = (
                select(DeviceStatus.name, func.count(Device.id).label("count"))
                .outerjoin(Device, Device.status_id == DeviceStatus.id)
                .group_by(DeviceStatus.id, DeviceStatus.name)
                .order_by(DeviceStatus.name)
            )

            total_devices_res = await db.execute(total_devices_stmt)
            types_res = await db.execute(types_stmt)
            statuses_res = await db.execute(statuses_stmt)

            total_devices = total_devices_res.scalar_one()
            device_types_list = [{"name": name, "count": count} for name, count in types_res.all()]
            device_statuses_list = [{"name": name, "count": count} for name, count in statuses_res.all()]

            return {
                "device_types_count": device_types_list,
                "device_statuses_count": device_statuses_list,
                "total_devices": total_devices,
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_dashboard_stats: {e}", exc_info=True)
            raise e

    async def create_device(self, db: AsyncSession, asset_data: AssetCreate, user_id: int) -> Device:
        try:
            asset_type = await db.get(AssetType, asset_data.asset_type_id)
            if not asset_type:
                raise NotFoundError(f"Тип актива с id={asset_data.asset_type_id} не найден.")

            prefix = asset_type.prefix
            date_str = datetime.utcnow().strftime("%Y%m%d")
            search_prefix = f"{prefix}-{date_str}-"
            last_device_stmt = (
                select(Device.inventory_number)
                .where(Device.inventory_number.like(f"{search_prefix}%"))
                .order_by(Device.inventory_number.desc())
                .limit(1)
            )
            last_inv_number = (await db.execute(last_device_stmt)).scalar_one_or_none()
            new_seq = int(last_inv_number.split("-")[-1]) + 1 if last_inv_number else 1
            inventory_number = f"{search_prefix}{new_seq:03d}"

            tags = []
            if asset_data.tag_ids:
                tag_stmt = select(Tag).where(Tag.id.in_(asset_data.tag_ids))
                tags = (await db.execute(tag_stmt)).scalars().all()

            device_dict = asset_data.model_dump(exclude={"tag_ids", "manufacturer_id"})
            device_dict["inventory_number"] = inventory_number

            device = Device(**device_dict)
            device.tags = tags

            db.add(device)
            await db.flush()

            await log_action(
                db=db,
                user_id=user_id,
                action_type="create",
                entity_type="Device",
                entity_id=device.id,
                details={
                    "inventory_number": device.inventory_number,
                    "name": device.name,
                },
            )
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            error_info = str(e.orig).lower() if e.orig else str(e).lower()
            if 'serial_number' in error_info:
                raise DuplicateDeviceError("Актив с таким серийным номером уже существует.")
            elif 'mac_address' in error_info:
                raise DuplicateDeviceError("Актив с таким MAC-адресом уже существует.")
            elif 'inventory_number' in error_info:
                raise DuplicateDeviceError(f"Актив с инвентарным номером {device.inventory_number} уже существует.")
            else:
                # Включаем детали ошибки для отладки
                raise DuplicateDeviceError(f"Актив с такими данными уже существует. Детали: {error_info}")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Ошибка при создании устройства: {e}", exc_info=True)
            raise e

        return await self.get_device_with_relations(db, device.id)

    async def bulk_delete_devices(self, db: AsyncSession, device_ids: list[int], user_id: int) -> tuple[int, list]:
        errors = []
        if not device_ids:
            return 0, errors

        stmt_select = select(Device).options(selectinload(Device.device_model)).where(Device.id.in_(device_ids))
        devices_to_delete = (await db.execute(stmt_select)).scalars().all()
        if not devices_to_delete:
            return 0, errors

        actual_device_ids = [d.id for d in devices_to_delete]
        try:
            for device in devices_to_delete:
                await log_action(
                    db=db,
                    user_id=user_id,
                    action_type="delete",
                    entity_type="Device",
                    entity_id=device.id,
                    details={
                        "inventory_number": device.inventory_number,
                        "name": device.name,
                    },
                )
            stmt_delete = delete(Device).where(Device.id.in_(actual_device_ids))
            delete_result = await db.execute(stmt_delete)
            await db.commit()
            return delete_result.rowcount, errors
        except SQLAlchemyError as e:
            await db.rollback()
            return 0, [str(e)]

    async def bulk_update_devices(
        self, db: AsyncSession, device_ids: list[int], update_data: dict, user_id: int
    ) -> int:
        if not device_ids or not update_data:
            return 0

        stmt_select = (
            select(Device)
            .options(
                selectinload(Device.status),
                selectinload(Device.department),
                selectinload(Device.location),
            )
            .where(Device.id.in_(device_ids))
        )
        old_devices = (await db.execute(stmt_select)).scalars().all()
        if not old_devices:
            return 0

        tasks = {
            "status": db.get(DeviceStatus, update_data["status_id"]) if "status_id" in update_data else None,
            "department": db.get(Department, update_data["department_id"]) if "department_id" in update_data else None,
            "location": db.get(Location, update_data["location_id"]) if "location_id" in update_data else None,
        }
        valid_tasks = {k: v for k, v in tasks.items() if v is not None}
        results = await asyncio.gather(*valid_tasks.values())
        new_related_models = dict(zip(valid_tasks.keys(), results, strict=False))

        try:
            for device in old_devices:
                diff = {}
                if "status" in new_related_models and device.status_id != new_related_models["status"].id:
                    diff["Статус"] = {
                        "old": device.status.name if device.status else "",
                        "new": new_related_models["status"].name,
                    }
                if "department" in new_related_models and device.department_id != new_related_models["department"].id:
                    diff["Отдел"] = {
                        "old": device.department.name if device.department else "",
                        "new": new_related_models["department"].name,
                    }
                if "location" in new_related_models and device.location_id != new_related_models["location"].id:
                    diff["Местоположение"] = {
                        "old": device.location.name if device.location else "",
                        "new": new_related_models["location"].name,
                    }

                if diff:
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action_type="update",
                        entity_type="Device",
                        entity_id=device.id,
                        details={"diff": diff, "source": "bulk_update"},
                    )
            stmt_update = update(Device).where(Device.id.in_(device_ids)).values(**update_data)
            update_result = await db.execute(stmt_update)
            await db.commit()
            return update_result.rowcount
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def delete_device_with_audit(self, db: AsyncSession, device_id: int, user_id: int):
        device = (await db.execute(select(Device).where(Device.id == device_id))).scalar_one_or_none()
        if not device:
            raise DeviceNotFoundException(f"Устройство с id={device_id} не найдено.")

        try:
            await log_action(
                db=db,
                user_id=user_id,
                action_type="delete",
                entity_type="Device",
                entity_id=device.id,
                details={
                    "inventory_number": device.inventory_number,
                    "name": device.name,
                },
            )
            await db.delete(device)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise e
