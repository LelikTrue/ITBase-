# app/schemas/supplier.py

from pydantic import BaseModel, ConfigDict


class SupplierBase(BaseModel):
    name: str
    description: str | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(SupplierBase):
    pass


class SupplierResponse(SupplierBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
