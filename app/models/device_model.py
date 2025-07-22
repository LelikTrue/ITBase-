from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base, BaseMixin

class DeviceModel(Base, BaseMixin):
    __tablename__ = "DeviceModel"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    manufacturer_id = Column(Integer, ForeignKey("Manufacturer.id"), nullable=False)
    asset_type_id = Column(Integer, ForeignKey("AssetType.id"), nullable=False)
    description = Column(String(500))
    specification = Column(JSON)
    
    # Relationships
    manufacturer = relationship("Manufacturer", back_populates="device_models")
    devices = relationship("Device", back_populates="device_model")
    asset_type = relationship("AssetType", back_populates="device_models")
