# app/models/asset.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, JSON, Date
from sqlalchemy.orm import relationship
from app.db.database import Base # Убедитесь, что это правильный импорт Base
import datetime

# --- Вспомогательные модели (определены до Device) ---

class Manufacturer(Base):
    __tablename__ = "Manufacturer"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    device_models = relationship("DeviceModel", back_populates="manufacturer")

class DeviceModel(Base):
    __tablename__ = "DeviceModel"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    manufacturer_id = Column(Integer, ForeignKey("Manufacturer.id"), nullable=False)
    asset_type_id = Column(Integer, ForeignKey("AssetType.id"), nullable=False)
    description = Column(String(500))
    specification = Column(JSON)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    manufacturer = relationship("Manufacturer", back_populates="device_models")
    devices = relationship("Device", back_populates="device_model")

class Department(Base):
    __tablename__ = "Department"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    devices_in_department = relationship("Device", back_populates="department")

class Location(Base):
    __tablename__ = "Location"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    devices_at_location = relationship("Device", back_populates="location")

class Employee(Base):
    __tablename__ = "Employee"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    patronymic = Column(String(255))
    employee_id = Column(String(255), unique=True)
    email = Column(String(255), unique=True, index=True)
    phone_number = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    assigned_devices = relationship("Device", back_populates="employee")

# --- Основные модели ---

class AssetType(Base):
    __tablename__ = "AssetType"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    devices = relationship("Device", back_populates="asset_type")

class DeviceStatus(Base):
    __tablename__ = "DeviceStatus"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    devices = relationship("Device", back_populates="status")

# ЕДИНСТВЕННОЕ И ПРАВИЛЬНОЕ ОПРЕДЕЛЕНИЕ КЛАССА DEVICE
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
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    attributes = Column(JSON)

    device_model_id = Column(Integer, ForeignKey("DeviceModel.id"), nullable=False)
    asset_type_id = Column(Integer, ForeignKey("AssetType.id"), nullable=False)
    status_id = Column(Integer, ForeignKey("DeviceStatus.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("Department.id"))
    location_id = Column(Integer, ForeignKey("Location.id"))
    employee_id = Column(Integer, ForeignKey("Employee.id"))

    # Отношения (relationship)
    device_model = relationship("DeviceModel", back_populates="devices")
    asset_type = relationship("AssetType", back_populates="devices")
    status = relationship("DeviceStatus", back_populates="devices")
    department = relationship("Department", back_populates="devices_in_department")
    location = relationship("Location", back_populates="devices_at_location")
    employee = relationship("Employee", back_populates="assigned_devices")
    attachments = relationship("Attachment", back_populates="device") # <-- ТЕПЕРЬ ОНО ЗДЕСЬ

# --- НОВЫЕ МОДЕЛИ: Attachment и ActionLog ---

class Attachment(Base):
    __tablename__ = "Attachment"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("Device.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100))
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    device = relationship("Device", back_populates="attachments")

class ActionLog(Base):
    __tablename__ = "ActionLog"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    user_id = Column(Integer)
    action_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)