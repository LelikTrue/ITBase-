from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, BaseMixin

class AssetType(Base, BaseMixin):
    __tablename__ = "AssetType"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    
    # Relationships
    devices = relationship("Device", back_populates="asset_type")
    device_models = relationship("DeviceModel", back_populates="asset_type")
