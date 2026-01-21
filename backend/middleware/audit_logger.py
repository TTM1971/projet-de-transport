"""
Helper pour logger les actions dans l'audit
"""
from sqlalchemy.orm import Session
from models.audit_log import AuditLog as AuditLogModel
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request

def log_audit(
    db: Session,
    action: str,
    resource_type: str,
    user_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    severity: str = "info",
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
):
    """Logger une action dans l'audit"""
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    
    audit_log = AuditLogModel(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
        severity=severity
    )
    
    db.add(audit_log)
    db.commit()
    return audit_log
