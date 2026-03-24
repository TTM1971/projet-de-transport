from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String)  # Rôle par défaut (pour compatibilité, sera remplacé par roles relation)
    
    # Informations personnelles
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    ville = Column(String, index=True)
    avatar_url = Column(String)
    
    # Organisation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Dates et statut
    hire_date = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Préférences
    preferences = Column(JSON)  # {"language": "fr", "notifications": {...}}
    
    # Relations
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    organization = relationship("Organization", back_populates="users")
    
    def __repr__(self):
        return f"<User {self.username}>"
