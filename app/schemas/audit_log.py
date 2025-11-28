from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ActionLogBase(BaseModel):
    user_id: int | None = None
    action_type: str
    entity_type: str
    entity_id: int
    details: dict[str, Any] = {}


class ActionLogCreate(ActionLogBase):
    pass


class ActionLog(ActionLogBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
