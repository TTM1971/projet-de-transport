from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserLogin, UserResponse
from models.user import User
from models.session import Session as SessionModel
from models.password_reset_token import PasswordResetToken
from database import get_db
from auth.jwt_handler import create_access_token
from auth.hash_password import hash_password, verify_password
from middleware.audit_logger import log_audit
from middleware.dependencies import get_current_user
from datetime import datetime, timedelta
from jose import jwt
import uuid
from typing import Optional

router = APIRouter()


def _normalize_city(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = v.strip()
    return s if s else None


@router.post("/register", response_model=UserResponse)
def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Inscription d'un nouvel utilisateur"""
    user_exist = db.query(User).filter(User.username == user_data.username).first()
    if user_exist:
        log_audit(db, "register", "User", details={"error": "Username already exists", "username": user_data.username}, severity="warning", request=request)
        raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
    
    # Vérifier email unique si fourni
    if user_data.email:
        email_exist = db.query(User).filter(User.email == user_data.email).first()
        if email_exist:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")

    ville = _normalize_city(user_data.ville)
    if not ville:
        raise HTTPException(status_code=400, detail="La ville est obligatoire")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        ville=ville,
        organization_id=user_data.organization_id,
        is_active=False  # Nouveaux comptes sont inactifs par défaut, nécessitent approbation
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    log_audit(db, "register", "User", user_id=user.id, resource_id=user.id, severity="info", request=request)
    return user

@router.post("/login")
def login(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Connexion d'un utilisateur"""
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user:
        log_audit(db, "login", "User", details={"error": "User not found", "username": user_data.username}, severity="warning", request=request)
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    
    if not user.is_active:
        log_audit(db, "login", "User", user_id=user.id, details={"error": "Account disabled"}, severity="warning", request=request)
        raise HTTPException(status_code=403, detail="Compte désactivé")
    
    if not verify_password(user_data.password, user.hashed_password):
        log_audit(db, "login", "User", user_id=user.id, details={"error": "Invalid password"}, severity="error", request=request)
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    
    # Créer le token
    token_data = {
        "sub": user.username,
        "role": user.role or "agent",
        "jti": str(uuid.uuid4())  # JWT ID pour la session
    }
    token = create_access_token(token_data, expires_delta=timedelta(hours=24))
    
    # Décoder le token pour obtenir le jti
    payload = jwt.decode(token, "monsecret", algorithms=["HS256"])
    jti = payload.get("jti")
    expires_at = datetime.fromtimestamp(payload.get("exp"))
    
    # Créer la session
    session = SessionModel(
        id=jti,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=expires_at
    )
    db.add(session)
    
    # Mettre à jour last_login
    user.last_login = datetime.utcnow()
    
    db.commit()
    
    log_audit(db, "login", "User", user_id=user.id, severity="info", request=request)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "ville": user.ville,
        }
    }

@router.post("/logout")
def logout(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Déconnexion (fermer la session actuelle)"""
    # Dans une implémentation complète, on récupérerait le jti du token
    # Pour l'instant, on log juste l'action
    log_audit(db, "logout", "User", user_id=current_user.id, severity="info", request=request)
    return {"message": "Déconnexion réussie"}

@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    """Obtenir les informations de l'utilisateur actuel"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone": current_user.phone,
        "ville": current_user.ville,
        "role": current_user.role,
        "organization_id": current_user.organization_id,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login
    }

@router.post("/forgot-password")
def forgot_password(
    email: str,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Demander une réinitialisation de mot de passe"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Ne pas révéler si l'email existe ou non (sécurité)
        return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé"}
    
    # Générer un token de réinitialisation
    reset_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Désactiver les anciens tokens
    old_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at == None
    ).all()
    for old_token in old_tokens:
        old_token.used_at = datetime.utcnow()
    
    # Créer le nouveau token
    reset_token_obj = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    db.add(reset_token_obj)
    db.commit()
    
    log_audit(db, "password_reset_requested", "User", user_id=user.id, severity="info", request=request)
    
    # TODO: Envoyer email avec le lien de réinitialisation
    # Pour l'instant, on retourne le token (à ne pas faire en production)
    return {"message": "Token de réinitialisation créé", "token": reset_token}  # À retirer en production

@router.post("/reset-password/{token}")
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Réinitialiser le mot de passe avec un token"""
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used_at == None,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")
    
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Mettre à jour le mot de passe
    user.hashed_password = hash_password(new_password)
    reset_token.used_at = datetime.utcnow()
    
    db.commit()
    
    log_audit(db, "password_reset", "User", user_id=user.id, severity="info", request=request)
    
    return {"message": "Mot de passe réinitialisé avec succès"}

@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Changer le mot de passe (utilisateur connecté)"""
    if not verify_password(old_password, current_user.hashed_password):
        log_audit(db, "password_change", "User", user_id=current_user.id, details={"error": "Invalid old password"}, severity="warning", request=request)
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")
    
    current_user.hashed_password = hash_password(new_password)
    db.commit()
    
    log_audit(db, "password_change", "User", user_id=current_user.id, severity="info", request=request)
    
    return {"message": "Mot de passe changé avec succès"}
