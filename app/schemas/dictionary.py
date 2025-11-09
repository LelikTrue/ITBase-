from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional

# --- Базовые схемы ---

class DictionarySimpleCreate(BaseModel):
    """Схема для простых справочников (имя, описание)."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)

class DictionarySimpleUpdate(BaseModel):
    """Схема для обновления простых справочников."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)

# --- Схемы для конкретных справочников ---

class DeviceStatusCreate(DictionarySimpleCreate):
    pass

class ManufacturerCreate(DictionarySimpleCreate):
    pass

class DepartmentCreate(DictionarySimpleCreate):
    pass

class LocationCreate(DictionarySimpleCreate):
    pass

class SupplierCreate(BaseModel):
    name: str = Field(..., max_length=100)
    contact_person: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=255)


# ===============================================================
# DeviceModel
# ===============================================================
class DeviceModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    manufacturer_id: int
    asset_type_id: int
    description: str | None = Field(None, max_length=255)

    @field_validator('name', 'description', mode='before')
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        """Удаляет начальные и конечные пробелы из строковых полей."""
        if isinstance(v, str):
            return v.strip()
        return v


class DeviceModelUpdate(DeviceModelCreate):
    pass

# ===============================================================
# Employee
# ===============================================================
class EmployeeCreate(BaseModel):
    # --- ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ---
    last_name: str = Field(..., max_length=50, description="Фамилия")
    first_name: str = Field(..., max_length=50, description="Имя")

    # --- ОПЦИОНАЛЬНЫЕ ПОЛЯ ---
    patronymic: Optional[str] = Field(None, max_length=50)
    employee_id: Optional[str] = Field(None, max_length=50) # Сделали опциональным
    position: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    department_id: Optional[int] = Field(None)

    # --- ВАЛИДАТОР ДЛЯ ПРЕОБРАЗОВАНИЯ ПУСТЫХ СТРОК В NONE ---
    @field_validator(
        'patronymic', 'employee_id', 'position', 'email', 
        'phone_number', 'department_id', 
        mode='before'
    )
    @classmethod
    def empty_str_to_none(cls, v):
        """
        Преобразует пустую строку, пришедшую из формы, в None.
        Это позволяет опциональным полям (включая EmailStr) 
        корректно проходить валидацию, если они не заполнены.
        """
        if v == '':
            return None
        return v

class EmployeeUpdate(EmployeeCreate):
    """Схема обновления наследует всю логику и поля от схемы создания."""
    pass


# ===============================================================
# AssetType
# ===============================================================
class AssetTypeCreate(DictionarySimpleCreate):
    """Схема для создания типа актива, включая префикс."""
    prefix: str = Field(..., max_length=10)

class AssetTypeUpdate(AssetTypeCreate):
    """Схема для обновления типа актива. Наследует все поля от Create."""


# ===============================================================
# Схемы для ответов (Response)
# ===============================================================
class DictionarySimpleResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)

class DeviceModelResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    manufacturer: 'DictionarySimpleResponse'
    asset_type: 'DictionarySimpleResponse'

    model_config = ConfigDict(from_attributes=True)

class EmployeeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    patronymic: str | None = None
    position: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    employee_id: Optional[str] # Также делаем опциональным в ответе

    model_config = ConfigDict(from_attributes=True)

class AssetTypeResponse(DictionarySimpleResponse):
    """Схема для ответа с типом актива, включая префикс."""
    prefix: str