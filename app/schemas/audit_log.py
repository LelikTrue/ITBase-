from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel

class ActionLogBase(BaseModel):
    user_id: Optional[int] = None
    action_type: str
    entity_type: str
    entity_id: int
    details: Dict[str, Any] = {}

class ActionLogCreate(ActionLogBase):
    pass

class ActionLog(ActionLogBase):
    id: int
    timestamp: datetime
    
    class Config:
        orm_mode = True
