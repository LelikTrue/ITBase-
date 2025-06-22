from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
import logging # Import logging

from .. import models
from ..schemas.device import DeviceCreate, DeviceUpdate
from ..db.database import get_db

# Настройка логирования
logger = logging.getLogger(__name__)


class DeviceService:
    """Сервис для работы с устройствами."""
    
    @staticmethod # Keep staticmethod for now, but consider making it a class method or instance method if state is needed
    def get_device(db: Session, device_id: int) -> Optional[models.Device]:
        """
        Получает устройство по ID с загрузкой связанных данных.
        
        Args:
            db: Сессия базы данных
            device_id: ID устройства
            
        Returns:
            Optional[models.Device]: Найденное устройство или None
        """
        try:
            return db.query(models.Device)\
                .options(
                    joinedload(models.Device.device_model).joinedload(models.DeviceModel.manufacturer),
                    joinedload(models.Device.asset_type),
                    joinedload(models.Device.status),
                    joinedload(models.Device.department),
                    joinedload(models.Device.location),
                    joinedload(models.Device.employee)
                )\
                .filter(models.Device.id == device_id)\
                .first()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении устройства с ID {device_id}: {e}")
            raise
    
    @staticmethod
    def get_device_by_inventory_number(db: Session, inventory_number: str) -> Optional[models.Device]:
        """
        Получает устройство по инвентарному номеру.
        
        Args:
            db: Сессия базы данных
            inventory_number: Инвентарный номер
            
        Returns:
            Optional[models.Device]: Найденное устройство или None
        """
        try:
            return db.query(models.Device)\
                .filter(models.Device.inventory_number == inventory_number)\
                .first()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении устройства с инвентарным номером {inventory_number}: {e}")
            raise
    
    @staticmethod
    def get_devices(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[models.Device]:
        """
        Получает список устройств с пагинацией и фильтрацией.
        
        Args:
            db: Сессия базы данных
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            **filters: Параметры фильтрации (asset_type_id, status_id, и т.д.)
            
        Returns:
            List[models.Device]: Список устройств
        """
        try:
            query = db.query(models.Device)
            
            # Применяем фильтры, если они переданы
            for key, value in filters.items():
                if value is not None:
                    column = getattr(models.Device, key, None)
                    if column is not None:
                        query = query.filter(column == value)
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении списка устройств: {e}")
            raise
    
    @staticmethod
    def create_device(db: Session, device_data: DeviceCreate) -> models.Device:
        """
        Создает новое устройство.
        
        Args:
            db: Сессия базы данных
            device_data: Данные для создания устройства
            
        Returns:
            models.Device: Созданное устройство
            
        Raises:
            ValueError: Если устройство с таким инвентарным номером уже существует
        """
        # Проверяем, существует ли устройство с таким инвентарным номером
        if DeviceService.get_device_by_inventory_number(db, device_data.inventory_number):
            raise ValueError(f"Устройство с инвентарным номером {device_data.inventory_number} уже существует")
        
        try:
            # Создаем экземпляр модели из данных
            db_device = models.Device(**device_data.model_dump())
            
            # Добавляем в сессию и сохраняем
            db.add(db_device)
            db.commit()
            db.refresh(db_device)
            
            logger.info(f"Создано новое устройство с ID {db_device.id}")
            return db_device
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Ошибка при создании устройства: {e}")
            raise

    @staticmethod
    def update_device(
        db: Session,
        device_id: int,
        device_data: DeviceUpdate
    ) -> Optional[models.Device]:
        """
        Обновляет данные устройства.
        
        Args:
            db: Сессия базы данных
            device_id: ID обновляемого устройства
            device_data: Данные для обновления
            
        Returns:
            Optional[models.Device]: Обновленное устройство или None, если не найдено
        """
        try:
            # Получаем устройство
            db_device = DeviceService.get_device(db, device_id)
            if not db_device:
                return None
            
            # Обновляем только переданные поля
            update_data = device_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_device, field, value)
            
            db.commit()
            db.refresh(db_device)
            
            logger.info(f"Обновлено устройство с ID {device_id}")
            return db_device
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Ошибка при обновлении устройства с ID {device_id}: {e}")
            raise

    @staticmethod
    def delete_device(db: Session, device_id: int) -> bool:
        """
        Удаляет устройство.
        
        Args:
            db: Сессия базы данных
            device_id: ID удаляемого устройства
            
        Returns:
            bool: True, если удаление прошло успешно, иначе False
        """
        try:
            db_device = DeviceService.get_device(db, device_id)
            if not db_device:
                return False
            
            db.delete(db_device)
            db.commit()
            
            logger.info(f"Удалено устройство с ID {device_id}")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Ошибка при удалении устройства с ID {device_id}: {e}")
            raise