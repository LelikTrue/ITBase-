# app/schemas/dictionary.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List

# --- Базовые схемы ---

class DictionarySimpleCreate(BaseModel):
    """Схема для простых справочников (имя, описание)."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)

class DictionarySimpleUpdate(BaseModel):
    """Схема для обновления простых справочников."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)

# --- Схемы для конкретных справочников ---

# AssetType, DeviceStatus, Manufacturer, Department, Location
# используют общие схемы DictionarySimpleCreate и DictionarySimpleUpdate

# ===============================================================
# DeviceModel
# ===============================================================
class DeviceModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    manufacturer_id: int
    asset_type_id: int
    description: Optional[str] = Field(None, max_length=255)

    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    @field_validator("name", "description", mode='before')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Удаляет начальные и конечные пробелы из строковых полей."""
        if isinstance(v, str):
            return v.strip()
        return v
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---


class DeviceModelUpdate(DeviceModelCreate):
    pass
# Employee
class EmployeeCreate(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    patronymic: Optional[str] = Field(None, max_length=50)
    employee_id: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)

class DictionarySimpleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DeviceModelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    manufacturer: "DictionarySimpleResponse"
    asset_type: "DictionarySimpleResponse"

    model_config = ConfigDict(from_attributes=True)

class EmployeeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    employee_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeUpdate(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    patronymic: Optional[str] = Field(None, max_length=50)
    employee_id: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)

# --- ДОБАВЬ ЭТИ ДВА КЛАССА В КОНЕЦ ФАЙЛА ---

class AssetTypeCreate(DictionarySimpleCreate):
    """Схема для создания типа актива, включая префикс."""
    prefix: str = Field(..., max_length=10)

class AssetTypeUpdate(AssetTypeCreate):
    """Схема для обновления типа актива. Наследует все поля от Create."""
    pass

class AssetTypeResponse(DictionarySimpleResponse):
    """Схема для ответа с типом актива, включая префикс."""
    prefix: str