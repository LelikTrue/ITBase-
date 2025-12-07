from pydantic import BaseModel


class BaseDictItem(BaseModel):
    slug: str
    name: str
    description: str | None = None
    prefix: str | None = None


class InitialDataSchema(BaseModel):
    asset_types: list[BaseDictItem]
    device_statuses: list[BaseDictItem]
    departments: list[BaseDictItem]
    locations: list[BaseDictItem]
