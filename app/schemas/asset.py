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