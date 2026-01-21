from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    resource = Column(String, nullable=False, index=True)  # bus, ligne, billet, user, etc.
    action = Column(String, nullable=False)  # create, read, update, delete, export
    description = Column(String)
    
    # Relations
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission {self.resource}:{self.action}>"
