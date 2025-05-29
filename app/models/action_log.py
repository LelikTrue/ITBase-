from sqlalchemy import Column, Integer, String, JSON

from .base import Base, BaseMixin

class ActionLog(Base, BaseMixin):
    __tablename__ = "ActionLog"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Integer, nullable=False)
    user_id = Column(Integer)
    action_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    details = Column(JSON)
