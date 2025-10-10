# app/schemas/asset.py

from pydantic import BaseModel, Field, ConfigDict, model_validator
from fastapi import Form
from typing import Optional, Any, List
from datetime import date

# Импортируем схемы для вложенных ответов
from .dictionary import DictionarySimpleResponse, DeviceModelResponse, EmployeeResponse
from .tag import TagResponse

# --- Вспомогательный декоратор (остается без изменений) ---
def form_body(cls):
    """
    Декоратор, который позволяет Pydantic-модели принимать данные из формы.
    """
    # Этот декоратор сломается с List[int], так как Form() не умеет парсить списки.
    # Мы его пока оставим, но для полей со списками он не будет работать из коробки.
    # Это мы решим позже на уровне роутера.
    cls.__signature__ = cls.__signature__.replace(
        parameters=[
            arg.replace(default=Form(arg.default) if arg.default is not ... else Form(...))
            for arg in cls.__signature__.parameters.values()
        ]
    )
    return cls

# --- СОЗДАЕМ НОВУЮ БАЗОВУЮ МОДЕЛЬ ДЛЯ ФОРМ ---
class BaseFormModel(BaseModel):
    """
    Базовая модель для всех схем, получающих данные из HTML-форм.
    Автоматически преобразует пустые строки в None.
    """
    @model_validator(mode='before')
    @classmethod
    def empty_str_to_none(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key, value in data.items():
                if value == "":
                    data[key] = None
        return data

# --- Базовые поля для Актива ---
class AssetBase(BaseModel):
    # inventory_number: str = Field(max_length=255) # <--- УДАЛЕНО!
    serial_number: Optional[str] = Field(None, max_length=255)
    mac_address: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    source: str = Field("purchase", max_length=50)
    purchase_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    price: Optional[float] = Field(None, ge=0)
    
    # Связи через ID
    asset_type_id: int
    device_model_id: int
    status_id: int
    department_id: Optional[int] = None
    location_id: Optional[int] = None
    employee_id: Optional[int] = None
    
    # !# 2. ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ПРИЕМА ID ТЕГОВ #!
    # Мы не можем использовать декоратор form_body для этого поля,
    # так как HTML-формы не умеют отправлять списки чисел напрямую.
    # Мы будем обрабатывать это в роутере.
    tag_ids: List[int] = Field(default_factory=list)

# --- Схема для создания Актива ---
class AssetCreate(AssetBase, BaseFormModel): 
    """Схема для создания нового актива. Наследует все поля из AssetBase."""
    pass

# --- Схема для обновления Актива ---
# @form_body # Временно отключаем
class AssetUpdate(BaseFormModel):
    """
    Схема для обновления актива. Все поля опциональны.
    """
    inventory_number: Optional[str] = Field(None, max_length=255) # В обновлении он может быть, но только для чтения
    serial_number: Optional[str] = Field(None, max_length=255)
    mac_address: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    source: Optional[str] = Field(None, max_length=50)
    purchase_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    price: Optional[float] = Field(None, ge=0)
    
    asset_type_id: Optional[int] = None
    device_model_id: Optional[int] = None
    status_id: Optional[int] = None
    department_id: Optional[int] = None
    location_id: Optional[int] = None
    employee_id: Optional[int] = None
    
    # !# 2. ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ПРИЕМА ID ТЕГОВ #!
    tag_ids: Optional[List[int]] = None


# --- Схема для ответа API (самая важная) ---
class AssetResponse(AssetBase):
    """
    "Богатая" схема для возврата данных об активе.
    Включает вложенные объекты для связанных сущностей.
    """
    id: int
    inventory_number: str # А вот в ответе инвентарный номер ОБЯЗАТЕЛЬНО должен быть
    
    # Переопределяем поля с _id на полные объекты
    asset_type: DictionarySimpleResponse
    device_model: DeviceModelResponse
    status: DictionarySimpleResponse
    department: Optional[DictionarySimpleResponse] = None
    location: Optional[DictionarySimpleResponse] = None
    employee: Optional[EmployeeResponse] = None
    
    # !# 3. ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ОТОБРАЖЕНИЯ ПОЛНЫХ ОБЪЕКТОВ ТЕГОВ #!
    tags: List[TagResponse] = []
    
    model_config = ConfigDict(from_attributes=True)