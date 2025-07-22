from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, BaseMixin

class Manufacturer(Base, BaseMixin):
    __tablename__ = "Manufacturer"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    
    # Relationships
    device_models = relationship("DeviceModel", back_populates="manufacturer")
