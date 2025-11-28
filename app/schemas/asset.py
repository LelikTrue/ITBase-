# app/schemas/asset.py

from datetime import date
from typing import Any

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Импортируем схемы для вложенных ответов
from .dictionary import (
    DeviceModelResponse,
    DictionarySimpleResponse,
    EmployeeResponse,
)
from .tag import TagResponse


# --- Вспомогательный декоратор и базовая модель для форм  ---
def form_body(cls: type) -> type:
    cls.__signature__ = cls.__signature__.replace(
        parameters=[
            arg.replace(
                default=Form(arg.default) if arg.default is not ... else Form(...)
            )
            for arg in cls.__signature__.parameters.values()
        ]
    )
    return cls


class BaseFormModel(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key, value in data.items():
                if value == "":
                    data[key] = None
        return data


# --- Базовые поля для Актива ---
class AssetBase(BaseModel):
    name: str = Field(max_length=255)
    serial_number: str | None = Field(None, max_length=255)
    mac_address: str | None = Field(None, max_length=255)
    ip_address: str | None = Field(None, max_length=255)
    notes: str | None = None
    source: str | None = Field(None, max_length=50)  #!# ИЗМЕНЕНО: Сделано опциональным
    purchase_date: date | None = None
    warranty_end_date: date | None = None
    price: float | None = Field(None, ge=0)
    supplier_id: int | None = None
    current_wear_percentage: int | None = Field(
        None, ge=0, le=100, description="Процент износа от 0 до 100"
    )
    expected_lifespan_years: int | None = Field(
        None, ge=0, description="Ожидаемый срок службы в годах"
    )

    # Связи через ID
    asset_type_id: int
    device_model_id: int
    status_id: int
    department_id: int | None = None
    location_id: int | None = None
    employee_id: int | None = None

    tag_ids: list[int] = Field(default_factory=list)


# --- Схема для создания Актива ---
class AssetCreate(
    BaseFormModel, AssetBase
):  #!# Порядок наследования для корректной работы валидатора
    """Схема для создания нового актива. Наследует все поля из AssetBase."""

    # Все поля уже определены в AssetBase


# --- Схема для обновления Актива ---
class AssetUpdate(BaseFormModel):
    """
    Схема для обновления актива. Все поля опциональны.
    """

    name: str | None = Field(None, max_length=255)
    inventory_number: str | None = Field(
        None, max_length=255
    )  # Только для чтения в форме
    serial_number: str | None = Field(None, max_length=255)
    mac_address: str | None = Field(None, max_length=255)
    ip_address: str | None = Field(None, max_length=255)
    notes: str | None = None
    source: str | None = Field(None, max_length=50)
    purchase_date: date | None = None
    warranty_end_date: date | None = None
    price: float | None = Field(None, ge=0)
    supplier_id: int | None = None
    current_wear_percentage: int | None = Field(None, ge=0, le=100)
    expected_lifespan_years: int | None = Field(None, ge=0)
    asset_type_id: int | None = None
    device_model_id: int | None = None
    status_id: int | None = None
    department_id: int | None = None
    location_id: int | None = None
    employee_id: int | None = None
    tag_ids: list[int] | None = None


# --- Схема для ответа API ---
class AssetResponse(AssetBase):
    """
    "Богатая" схема для возврата данных об активе.
    Включает вложенные объекты для связанных сущностей.
    """

    id: int
    inventory_number: str

    # Переопределяем поля с _id на полные объекты
    asset_type: DictionarySimpleResponse
    device_model: DeviceModelResponse
    status: DictionarySimpleResponse
    department: DictionarySimpleResponse | None = None
    location: DictionarySimpleResponse | None = None
    employee: EmployeeResponse | None = None
    tags: list[TagResponse] = []

    # --- ДОБАВЛЕННЫЕ ПОЛЯ ДЛЯ ОТОБРАЖЕНИЯ ---
    # Поставщик будет загружен как связанный объект
    supplier: DictionarySimpleResponse | None = None

    model_config = ConfigDict(from_attributes=True)
