from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, BaseMixin

class Employee(Base, BaseMixin):
    __tablename__ = "Employee"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    patronymic = Column(String(255))
    employee_id = Column(String(255), unique=True)
    email = Column(String(255), unique=True, index=True)
    phone_number = Column(String(255))
    
    # Relationships
    assigned_devices = relationship("Device", back_populates="employee")
