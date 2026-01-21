from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # NULL si action système
    action = Column(String, nullable=False, index=True)  # login, logout, create, update, delete, export
    resource_type = Column(String, nullable=False, index=True)  # User, Bus, Billet, etc.
    resource_id = Column(Integer, index=True)
    ip_address = Column(String)
    user_agent = Column(String)
    details = Column(JSON)  # Données avant/après, erreurs, etc.
    severity = Column(String, default="info", index=True)  # info, warning, error, critical
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} on {self.resource_type} by user {self.user_id}>"
