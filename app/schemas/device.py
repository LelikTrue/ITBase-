from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class DeviceBase(BaseModel):
    """Базовая схема устройства."""
    inventory_number: str = Field(..., min_length=1, max_length=255)
    serial_number: Optional[str] = Field(None, max_length=255)
    mac_address: Optional[str] = Field(None, max_length=17)
    ip_address: Optional[str] = Field(None, max_length=15)
    notes: Optional[str] = None
    source: str = Field(..., max_length=50)
    purchase_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    price: Optional[float] = Field(None, ge=0)
    expected_lifespan_years: Optional[int] = Field(None, ge=0)
    current_wear_percentage: Optional[float] = Field(None, ge=0, le=100)
    device_model_id: int = Field(..., gt=0)
    asset_type_id: int = Field(..., gt=0)
    status_id: int = Field(..., gt=0)
    department_id: Optional[int] = Field(None, gt=0)
    location_id: Optional[int] = Field(None, gt=0)
    employee_id: Optional[int] = Field(None, gt=0)

class DeviceCreate(DeviceBase):
    """Схема для создания устройства."""
    pass

class DeviceUpdate(BaseModel):
    """Схема для обновления устройства."""
    inventory_number: Optional[str] = Field(None, min_length=1, max_length=255)
    serial_number: Optional[str] = Field(None, max_length=255)
    mac_address: Optional[str] = Field(None, max_length=17)
    ip_address: Optional[str] = Field(None, max_length=15)
    notes: Optional[str] = None
    source: Optional[str] = Field(None, max_length=50)
    purchase_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    price: Optional[float] = Field(None, ge=0)
    expected_lifespan_years: Optional[int] = Field(None, ge=0)
    current_wear_percentage: Optional[float] = Field(None, ge=0, le=100)
    device_model_id: Optional[int] = Field(None, gt=0)
    asset_type_id: Optional[int] = Field(None, gt=0)
    status_id: Optional[int] = Field(None, gt=0)
    department_id: Optional[int] = Field(None, gt=0)
    location_id: Optional[int] = Field(None, gt=0)
    employee_id: Optional[int] = Field(None, gt=0)

class DeviceInDBBase(DeviceBase):
    """Базовая схема устройства в БД."""
    id: int

    model_config = ConfigDict(from_attributes=True)

class Device(DeviceInDBBase):
    """Схема для возврата устройства."""
    pass
