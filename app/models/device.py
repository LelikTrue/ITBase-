from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship

from .base import Base

class Device(Base):
    __tablename__ = "Device"
    
    id = Column(Integer, primary_key=True, index=True)
    inventory_number = Column(String(255), unique=True, nullable=False)
    serial_number = Column(String(255))
    mac_address = Column(String(255))
    ip_address = Column(String(255))
    notes = Column(Text)
    source = Column(String(50), nullable=False)
    purchase_date = Column(Date)
    warranty_end_date = Column(Date)
    price = Column(Numeric(10,2))
    expected_lifespan_years = Column(Integer)
    current_wear_percentage = Column(Numeric(5,2))
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    attributes = Column(JSON)
    
    # Foreign keys
    device_model_id = Column(Integer, ForeignKey("DeviceModel.id"), nullable=False)
    asset_type_id = Column(Integer, ForeignKey("AssetType.id"), nullable=False)
    status_id = Column(Integer, ForeignKey("DeviceStatus.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("Department.id"))
    location_id = Column(Integer, ForeignKey("Location.id"))
    employee_id = Column(Integer, ForeignKey("Employee.id"))
    
    # Relationships
    device_model = relationship("DeviceModel", back_populates="devices")
    asset_type = relationship("AssetType", back_populates="devices")
    status = relationship("DeviceStatus", back_populates="devices")
    department = relationship("Department", back_populates="devices_in_department")
    location = relationship("Location", back_populates="devices_at_location")
    employee = relationship("Employee", back_populates="assigned_devices")
    attachments = relationship("Attachment", back_populates="device")
