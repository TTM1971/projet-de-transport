from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from auth.jwt_handler import verify_token
from typing import List, Optional
from sqlalchemy.orm import Session
from database import get_db
from models.user import User as UserModel
from models.chauffeur import Chauffeur as ChauffeurModel
from middleware.audit_logger import log_audit

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Récupère l'utilisateur actuel à partir du token JWT"""
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Token invalide")
    
    # Récupérer l'utilisateur depuis la base de données
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    # Vérifier si l'utilisateur est actif (is_active peut être NULL pour compatibilité)
    if user.is_active is False:
        raise HTTPException(status_code=401, detail="Compte désactivé")
    
    return user

def require_role(allowed_roles: List[str]):
    """Vérifie que l'utilisateur a un des rôles autorisés"""
    def role_checker(user: UserModel = Depends(get_current_user)):
        user_role = user.role if hasattr(user, 'role') else None
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Accès interdit. Rôles autorisés: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker

def require_any_role(*roles: str):
    """Helper pour vérifier plusieurs rôles"""
    return require_role(list(roles))

# Permissions spécifiques par rôle
def require_admin():
    return require_role(["admin"])

def require_agent_or_admin():
    return require_role(["agent", "admin"])

def require_gestionnaire_or_admin():
    return require_role(["gestionnaire", "admin"])

def require_maintenance_or_admin():
    return require_role(["maintenance", "admin"])

def require_gestionnaire_maintenance_or_admin():
    return require_role(["gestionnaire", "maintenance", "admin"])


def get_current_chauffeur_profile(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Utilisateur connecté avec rôle chauffeur + fiche Chauffeur liée (user_id)."""
    if getattr(current_user, "role", None) != "chauffeur":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux comptes chauffeur",
        )
    ch = db.query(ChauffeurModel).filter(ChauffeurModel.user_id == current_user.id).first()
    if not ch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profil chauffeur non lié à ce compte. Contactez un administrateur.",
        )
    return ch
