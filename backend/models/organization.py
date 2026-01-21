from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)  # compagnie, agence, gare
    parent_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # Hiérarchie
    
    # Adresse
    address = Column(String)
    city = Column(String)
    country = Column(String)
    phone = Column(String)
    email = Column(String)
    logo_url = Column(String)
    
    # Statut
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    parent = relationship("Organization", remote_side=[id], backref="children")
    users = relationship("User", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization {self.name} ({self.type})>"
