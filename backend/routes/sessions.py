from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.session import Session as SessionModel
from models.user import User as UserModel
from schemas.session import Session
from middleware.dependencies import get_current_user
from datetime import datetime, timedelta
from jose import jwt
from auth.jwt_handler import SECRET_KEY, ALGORITHM

router = APIRouter()

@router.get("/", response_model=List[Session])
def get_my_sessions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtenir mes sessions actives"""
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id,
        SessionModel.is_active == True,
        SessionModel.expires_at > datetime.utcnow()
    ).order_by(SessionModel.created_at.desc()).all()
    return sessions

@router.get("/admin/all", response_model=List[Session])
def get_all_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtenir toutes les sessions (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    sessions = db.query(SessionModel).filter(
        SessionModel.is_active == True,
        SessionModel.expires_at > datetime.utcnow()
    ).order_by(SessionModel.created_at.desc()).offset(skip).limit(limit).all()
    return sessions

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Fermer une session spécifique"""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    # L'utilisateur peut fermer ses propres sessions, l'admin peut fermer toutes les sessions
    if session.user_id != current_user.id and (not hasattr(current_user, 'role') or current_user.role != 'admin'):
        raise HTTPException(status_code=403, detail="Vous ne pouvez fermer que vos propres sessions")
    
    session.is_active = False
    db.commit()
    return None

@router.delete("/other/all", status_code=status.HTTP_204_NO_CONTENT)
def delete_other_sessions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Fermer toutes mes autres sessions (garder la session actuelle)"""
    # On ne peut pas identifier facilement la session actuelle depuis le token
    # Donc on ferme toutes les sessions sauf celles créées dans les 5 dernières minutes
    recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
    
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id,
        SessionModel.is_active == True,
        SessionModel.created_at < recent_cutoff
    ).all()
    
    for session in sessions:
        session.is_active = False
    
    db.commit()
    return None

@router.delete("/admin/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Fermer une session (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    session.is_active = False
    db.commit()
    return None
