from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session # Keep Session for now, as per user request to defer major changes

from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый класс для сервисов с CRUD операциями."""
    
    def __init__(self, model: Type[ModelType]):
        """
        Инициализация сервиса с указанием модели.
        
        Args:
            model: SQLAlchemy модель
        """
        self.model = model
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]: # Keep Session
        """Получить объект по ID."""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi( # Keep Session
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Получить список объектов с пагинацией."""
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType: # Keep Session
        """Создать новый объект."""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update( # Keep Session
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Обновить существующий объект."""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # For Pydantic v2, .dict() is .model_dump()
            # This ensures compatibility with both Pydantic v1 and v2
            if hasattr(obj_in, 'model_dump'):
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj) # add is synchronous
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: int) -> ModelType: # Keep Session
        """Удалить объект по ID."""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
