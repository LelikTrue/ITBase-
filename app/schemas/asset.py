# app/schemas/asset.py

from datetime import date
from typing import Any, Type

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Импортируем схемы для вложенных ответов
from .dictionary import DeviceModelResponse, DictionarySimpleResponse, EmployeeResponse
from .tag import TagResponse


# --- Вспомогательный декоратор (остается без изменений) ---
def form_body(cls: Type) -> Type:
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
                if value == '':
                    data[key] = None
        return data

# --- Базовые поля для Актива ---
class AssetBase(BaseModel):
    # !# ИЗМЕНЕНИЕ 1: Добавляем поле name
    name: str = Field(max_length=255)
    serial_number: str | None = Field(None, max_length=255)
    mac_address: str | None = Field(None, max_length=255)
    ip_address: str | None = Field(None, max_length=255)
    notes: str | None = None
    source: str = Field('purchase', max_length=50)
    purchase_date: date | None = None
    warranty_end_date: date | None = None
    price: float | None = Field(None, ge=0)

    # Связи через ID
    asset_type_id: int
    device_model_id: int
    status_id: int
    department_id: int | None = None
    location_id: int | None = None
    employee_id: int | None = None

    # !# 2. ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ПРИЕМА ID ТЕГОВ #!
    # Мы не можем использовать декоратор form_body для этого поля,
    # так как HTML-формы не умеют отправлять списки чисел напрямую.
    # Мы будем обрабатывать это в роутере.
    tag_ids: list[int] = Field(default_factory=list)

# --- Схема для создания Актива ---
class AssetCreate(AssetBase, BaseFormModel):
    """Схема для создания нового актива. Наследует все поля из AssetBase."""

# --- Схема для обновления Актива ---
# @form_body # Временно отключаем
class AssetUpdate(BaseFormModel):
    """
    Схема для обновления актива. Все поля опциональны.
    """
    # !# ИЗМЕНЕНИЕ 2: Добавляем опциональное поле name
    name: str | None = Field(None, max_length=255)
    inventory_number: str | None = Field(None, max_length=255) # В обновлении он может быть, но только для чтения
    serial_number: str | None = Field(None, max_length=255)
    mac_address: str | None = Field(None, max_length=255)
    ip_address: str | None = Field(None, max_length=255)
    notes: str | None = None
    source: str | None = Field(None, max_length=50)
    purchase_date: date | None = None
    warranty_end_date: date | None = None
    price: float | None = Field(None, ge=0)

    asset_type_id: int | None = None
    device_model_id: int | None = None
    status_id: int | None = None
    department_id: int | None = None
    location_id: int | None = None
    employee_id: int | None = None

    # !# 2. ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ПРИЕМА ID ТЕГОВ #!
    tag_ids: list[int] | None = None


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
    department: DictionarySimpleResponse | None = None
    location: DictionarySimpleResponse | None = None
    employee: EmployeeResponse | None = None

    # !# 3. ДОБАВЛЯЕМ ПОЛЕ ДЛЯ ОТОБРАЖЕНИЯ ПОЛНЫХ ОБЪЕКТОВ ТЕГОВ #!
    tags: list[TagResponse] = []

    model_config = ConfigDict(from_attributes=True)
