from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models # Импортируем все модели из app.models (через __init__.py)
from .. import schemas # Импортируем все схемы из app.schemas (через __init__.py)

def get_asset_type(db: Session, asset_type_id: int) -> Optional[models.AssetType]:
    """
    Получает тип актива по его ID.
    """
    return db.query(models.AssetType).filter(models.AssetType.id == asset_type_id).first()

def get_asset_type_by_name(db: Session, name: str) -> Optional[models.AssetType]:
    """
    Получает тип актива по его имени.
    """
    return db.query(models.AssetType).filter(models.AssetType.name == name).first()

def get_asset_types(db: Session, skip: int = 0, limit: int = 100) -> List[models.AssetType]:
    """
    Получает список типов активов с пагинацией.
    """
    return db.query(models.AssetType).offset(skip).limit(limit).all()

def create_asset_type(db: Session, asset_type: schemas.AssetTypeCreate) -> models.AssetType:
    """
    Создает новый тип актива.
    """
    db_asset_type = models.AssetType(name=asset_type.name, description=asset_type.description)
    db.add(db_asset_type)
    db.commit()
    db.refresh(db_asset_type)
    return db_asset_type

def update_asset_type(db: Session, asset_type_id: int, asset_type_update: schemas.AssetTypeUpdate) -> Optional[models.AssetType]:
    """
    Обновляет существующий тип актива.
    """
    db_asset_type = get_asset_type(db, asset_type_id)
    if db_asset_type:
        update_data = asset_type_update.model_dump(exclude_unset=True) # Pydantic v2
        # Для Pydantic v1: update_data = asset_type_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_asset_type, key, value)
        db.commit()
        db.refresh(db_asset_type)
    return db_asset_type

def delete_asset_type(db: Session, asset_type_id: int) -> Optional[models.AssetType]:
    """
    Удаляет тип актива.
    """
    db_asset_type = get_asset_type(db, asset_type_id)
    if db_asset_type:
        db.delete(db_asset_type)
        db.commit()
    return db_asset_type