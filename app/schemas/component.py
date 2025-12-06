from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ComponentBase(BaseModel):
    name: str
    serial_number: str | None = None
    manufacturer: str | None = None


class CpuItem(ComponentBase):
    type: Literal['cpu']
    cores: int
    threads: int
    base_clock_mhz: int | None = None


class RamItem(ComponentBase):
    type: Literal['ram']
    size_mb: int
    speed_mhz: int | None = None
    form_factor: str | None = None


class StorageItem(ComponentBase):
    type: Literal['storage']
    type_label: str  # SSD, HDD, NVMe
    capacity_gb: int
    interface: str | None = None


class GpuItem(ComponentBase):
    type: Literal['gpu']
    memory_mb: int | None = None


class MotherboardCreate(ComponentBase):
    type: Literal['motherboard']


ComponentItem = Annotated[
    CpuItem | RamItem | StorageItem | GpuItem | MotherboardCreate,
    Field(discriminator='type')
]
