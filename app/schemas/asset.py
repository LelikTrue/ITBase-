# app/schemas/asset.py
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date # Импортируем date
from typing import Optional, Any, Dict # Импортируем Dict для JSON

# Если у вас есть другие схемы, например для DeviceModel, Department, Employee, Location
# from .device_model import DeviceModelResponse # Пример

# --- Схемы для AssetType ---
class AssetTypeBase(BaseModel):
    name: str = Field(..., max_length=255) # Указываем max_length
    description: Optional[str] = Field(None, max_length=500)

class AssetTypeCreate(AssetTypeBase):
    pass

class AssetTypeResponse(AssetTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Схемы для DeviceStatus ---
class DeviceStatusBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=500)

class DeviceStatusCreate(DeviceStatusBase):
    pass

class DeviceStatusResponse(DeviceStatusBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Схемы для Device ---
class DeviceBase(BaseModel):
    inventory_number: str = Field(..., max_length=255)
    serial_number: Optional[str] = Field(None, max_length=255)
    mac_address: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None # Text не имеет max_length
    source: str = Field(..., max_length=50)
    purchase_date: Optional[date] = None # Используем date
    warranty_end_date: Optional[date] = None # Используем date
    price: Optional[float] = None # Pydantic будет конвертировать Numeric(10,2) в float
    expected_lifespan_years: Optional[int] = None
    current_wear_percentage: Optional[float] = None # float для Numeric(5,2)
    attributes: Optional[Dict[str, Any]] = None # Для JSONB

    device_model_id: int
    asset_type_id: int
    status_id: int # Соответствует колонке status_id в DB

    department_id: Optional[int] = None
    location_id: Optional[int] = None
    employee_id: Optional[int] = None

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    # Все поля опциональны для обновления
    inventory_number: Optional[str] = Field(None, max_length=255)
    serial_number: Optional[str] = Field(None, max_length=255)
    mac_address: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    source: Optional[str] = Field(None, max_length=50)
    purchase_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    price: Optional[float] = None
    expected_lifespan_years: Optional[int] = None
    current_wear_percentage: Optional[float] = None
    attributes: Optional[Dict[str, Any]] = None

    device_model_id: Optional[int] = None
    asset_type_id: Optional[int] = None
    status_id: Optional[int] = None

    department_id: Optional[int] = None
    location_id: Optional[int] = None
    employee_id: Optional[int] = None


class DeviceResponse(DeviceBase):
    id: int

    updated_at: datetime # Используем updated_at из модели Device

    # Вложенные схемы для связанных объектов
    asset_type: Optional[AssetTypeResponse] = None
    status: Optional[DeviceStatusResponse] = None # Имя 'status', а не 'asset_status'
    # Добавьте другие отношения, если они нужны в ответе API
    # device_model: Optional[DeviceModelResponse] = None # Требует схемы для DeviceModel
    # department: Optional[DepartmentResponse] = None
    # location: Optional[LocationResponse] = None
    # employee: Optional[EmployeeResponse] = None

    model_config = ConfigDict(from_attributes=True) # Для Pydantic v2