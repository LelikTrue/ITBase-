# app/services/component_service.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_polymorphic

from app.models.component import (
    Component,
    ComponentCPU,
    ComponentGPU,
    ComponentHistory,
    ComponentMotherboard,
    ComponentRAM,
    ComponentStorage,
)
from app.schemas.component import ComponentItem


class ComponentService:
    @staticmethod
    async def sync_components(
        session: AsyncSession, asset_id: int, items: list[ComponentItem]
    ) -> None:
        """
        Синхронизирует список компонентов для актива.
        Реализует логику Smart Sync:
        1. Загружает текущие компоненты.
        2. Сравнивает с новыми.
        3. Выполняет INSERT/UPDATE/DELETE.
        4. Записывает историю изменений.
        """
        # 1. Загружаем текущие компоненты
        poly = with_polymorphic(
            Component, [ComponentCPU, ComponentRAM, ComponentStorage, ComponentGPU, ComponentMotherboard]
        )
        stmt = select(poly).where(Component.asset_id == asset_id)
        result = await session.execute(stmt)
        existing_components = result.scalars().all()

        # Создаем мапу существующих компонентов
        existing_map = {
            (c.component_type, c.name, c.serial_number): c for c in existing_components
        }

        # 2. Обрабатываем входящие данные
        processed_keys = set()

        for item in items:
            key = (item.type, item.name, item.serial_number)
            processed_keys.add(key)

            existing = existing_map.get(key)

            if existing:
                if ComponentService._update_component(existing, item):
                    session.add(existing)
                    await ComponentService._log_history(
                        session, asset_id, 'UPDATE', item.model_dump()
                    )
            else:
                new_component = ComponentService._create_component(asset_id, item)
                if new_component:
                    session.add(new_component)
                    await ComponentService._log_history(
                        session, asset_id, 'ADD', item.model_dump()
                    )

        # 3. DELETE logic
        for key, component in existing_map.items():
            if key not in processed_keys:
                await session.delete(component)
                snapshot = {
                    'type': component.component_type,
                    'name': component.name,
                    'serial_number': component.serial_number,
                    'id': component.id
                }
                await ComponentService._log_history(
                    session, asset_id, 'REMOVE', snapshot
                )

    @staticmethod
    def _update_component(existing: Component, item: ComponentItem) -> bool:
        updated = False

        # Общие поля
        if existing.manufacturer != item.manufacturer:
            existing.manufacturer = item.manufacturer
            updated = True

        # Специфичные поля
        if item.type == 'cpu' and isinstance(existing, ComponentCPU):
            if ComponentService._update_cpu(existing, item):
                updated = True
        elif item.type == 'ram' and isinstance(existing, ComponentRAM):
            if ComponentService._update_ram(existing, item):
                updated = True
        elif item.type == 'storage' and isinstance(existing, ComponentStorage):
            if ComponentService._update_storage(existing, item):
                updated = True
        elif item.type == 'gpu' and isinstance(existing, ComponentGPU):
            if ComponentService._update_gpu(existing, item):
                updated = True

        return updated

    @staticmethod
    def _update_cpu(existing: ComponentCPU, item: ComponentItem) -> bool:
        updated = False
        if existing.cores != item.cores:
            existing.cores = item.cores
            updated = True
        if existing.threads != item.threads:
            existing.threads = item.threads
            updated = True
        if existing.base_clock_mhz != item.base_clock_mhz:
            existing.base_clock_mhz = item.base_clock_mhz
            updated = True
        return updated

    @staticmethod
    def _update_ram(existing: ComponentRAM, item: ComponentItem) -> bool:
        updated = False
        if existing.size_mb != item.size_mb:
            existing.size_mb = item.size_mb
            updated = True
        if existing.speed_mhz != item.speed_mhz:
            existing.speed_mhz = item.speed_mhz
            updated = True
        if existing.form_factor != item.form_factor:
            existing.form_factor = item.form_factor
            updated = True
        return updated

    @staticmethod
    def _update_storage(existing: ComponentStorage, item: ComponentItem) -> bool:
        updated = False
        if existing.type_label != item.type_label:
            existing.type_label = item.type_label
            updated = True
        if existing.capacity_gb != item.capacity_gb:
            existing.capacity_gb = item.capacity_gb
            updated = True
        if existing.interface != item.interface:
            existing.interface = item.interface
            updated = True
        return updated

    @staticmethod
    def _update_gpu(existing: ComponentGPU, item: ComponentItem) -> bool:
        updated = False
        if existing.memory_mb != item.memory_mb:
            existing.memory_mb = item.memory_mb
            updated = True
        return updated

    @staticmethod
    def _create_component(asset_id: int, item: ComponentItem) -> Component | None:
        if item.type == 'cpu':
            return ComponentCPU(
                asset_id=asset_id,
                component_type='cpu',
                name=item.name,
                serial_number=item.serial_number,
                manufacturer=item.manufacturer,
                cores=item.cores,
                threads=item.threads,
                base_clock_mhz=item.base_clock_mhz,
            )
        elif item.type == 'ram':
            return ComponentRAM(
                asset_id=asset_id,
                component_type='ram',
                name=item.name,
                serial_number=item.serial_number,
                manufacturer=item.manufacturer,
                size_mb=item.size_mb,
                speed_mhz=item.speed_mhz,
                form_factor=item.form_factor,
            )
        elif item.type == 'storage':
            return ComponentStorage(
                asset_id=asset_id,
                component_type='storage',
                name=item.name,
                serial_number=item.serial_number,
                manufacturer=item.manufacturer,
                type_label=item.type_label,
                capacity_gb=item.capacity_gb,
                interface=item.interface,
            )
        elif item.type == 'gpu':
            return ComponentGPU(
                asset_id=asset_id,
                component_type='gpu',
                name=item.name,
                serial_number=item.serial_number,
                manufacturer=item.manufacturer,
                memory_mb=item.memory_mb,
            )
        elif item.type == 'motherboard':
            return ComponentMotherboard(
                asset_id=asset_id,
                component_type='motherboard',
                name=item.name,
                serial_number=item.serial_number,
                manufacturer=item.manufacturer,
            )
        return None

    @staticmethod
    async def _log_history(
        session: AsyncSession, asset_id: int, change_type: str, snapshot: dict
    ) -> None:
        history = ComponentHistory(
            asset_id=asset_id,
            change_type=change_type,
            component_snapshot=snapshot
        )
        session.add(history)
