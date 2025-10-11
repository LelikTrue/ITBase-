# app/schemas/dictionary.py


from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

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

# AssetType, DeviceStatus, Manufacturer, Department, Location
# используют общие схемы DictionarySimpleCreate и DictionarySimpleUpdate

# ===============================================================
# DeviceModel
# ===============================================================
class DeviceModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    manufacturer_id: int
    asset_type_id: int
    description: str | None = Field(None, max_length=255)

    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    @field_validator('name', 'description', mode='before')
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
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
    patronymic: str | None = Field(None, max_length=50)
    employee_id: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    phone_number: str | None = Field(None, max_length=20)

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
    employee_id: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeUpdate(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    patronymic: str | None = Field(None, max_length=50)
    employee_id: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    phone_number: str | None = Field(None, max_length=20)

# --- ДОБАВЬ ЭТИ ДВА КЛАССА В КОНЕЦ ФАЙЛА ---

class AssetTypeCreate(DictionarySimpleCreate):
    """Схема для создания типа актива, включая префикс."""
    prefix: str = Field(..., max_length=10)

class AssetTypeUpdate(AssetTypeCreate):
    """Схема для обновления типа актива. Наследует все поля от Create."""

class AssetTypeResponse(DictionarySimpleResponse):
    """Схема для ответа с типом актива, включая префикс."""
    prefix: str
