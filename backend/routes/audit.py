from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models.audit_log import AuditLog as AuditLogModel
from models.user import User as UserModel
from schemas.audit_log import AuditLog, AuditLogCreate
from middleware.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[AuditLog])
def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[str] = None,  # Format YYYY-MM-DD
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Liste des logs d'audit (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    query = db.query(AuditLogModel)
    
    # Filtres
    if user_id:
        query = query.filter(AuditLogModel.user_id == user_id)
    if action:
        query = query.filter(AuditLogModel.action == action)
    if resource_type:
        query = query.filter(AuditLogModel.resource_type == resource_type)
    if severity:
        query = query.filter(AuditLogModel.severity == severity)
    
    # Filtres date
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AuditLogModel.created_at >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Format de date invalide pour start_date (utilisez YYYY-MM-DD)")
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(AuditLogModel.created_at < end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Format de date invalide pour end_date (utilisez YYYY-MM-DD)")
    
    logs = query.order_by(AuditLogModel.created_at.desc()).offset(skip).limit(limit).all()
    return logs

@router.get("/{log_id}", response_model=AuditLog)
def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Détails d'un log d'audit (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    log = db.query(AuditLogModel).filter(AuditLogModel.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log d'audit non trouvé")
    return log

@router.get("/stats/summary")
def get_audit_stats(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Statistiques des logs d'audit (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Total logs
    total_logs = db.query(AuditLogModel).filter(AuditLogModel.created_at >= since).count()
    
    # Par sévérité
    severities = db.query(AuditLogModel.severity).filter(AuditLogModel.created_at >= since).all()
    severity_count = {}
    for (sev,) in severities:
        severity_count[sev] = severity_count.get(sev, 0) + 1
    
    # Par action
    actions = db.query(AuditLogModel.action).filter(AuditLogModel.created_at >= since).all()
    action_count = {}
    for (act,) in actions:
        action_count[act] = action_count.get(act, 0) + 1
    
    # Tentatives de connexion échouées
    failed_logins = db.query(AuditLogModel).filter(
        and_(
            AuditLogModel.action == "login",
            AuditLogModel.severity == "error",
            AuditLogModel.created_at >= since
        )
    ).count()
    
    return {
        "total_logs": total_logs,
        "period_days": days,
        "by_severity": severity_count,
        "by_action": action_count,
        "failed_logins": failed_logins
    }

@router.get("/export/csv")
def export_audit_logs_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Exporter les logs d'audit en CSV (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    from fastapi.responses import Response
    
    query = db.query(AuditLogModel)
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(AuditLogModel.created_at >= start)
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(AuditLogModel.created_at < end)
    
    logs = query.order_by(AuditLogModel.created_at.desc()).all()
    
    # Générer CSV
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow([
        "ID", "Date", "User ID", "Action", "Resource Type", "Resource ID",
        "Severity", "IP Address", "User Agent"
    ])
    
    # Données
    for log in logs:
        writer.writerow([
            log.id,
            log.created_at.isoformat(),
            log.user_id or "",
            log.action,
            log.resource_type,
            log.resource_id or "",
            log.severity,
            log.ip_address or "",
            log.user_agent or ""
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
    )
