from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, BaseMixin

class Attachment(Base, BaseMixin):
    __tablename__ = "Attachment"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("Device.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100))
    
    # Relationships
    device = relationship("Device", back_populates="attachments")
