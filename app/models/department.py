from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, BaseMixin

class Department(Base, BaseMixin):
    __tablename__ = "Department"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    
    # Relationships
    devices_in_department = relationship("Device", back_populates="department")
