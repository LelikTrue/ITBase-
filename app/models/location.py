from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, BaseMixin

class Location(Base, BaseMixin):
    __tablename__ = "Location"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    
    # Relationships
    devices_at_location = relationship("Device", back_populates="location")
