from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import delete
from typing import List, Optional
from database import get_db
from models.user import User as UserModel
from models.session import Session as SessionModel
from models.password_reset_token import PasswordResetToken
from models.user_role import user_roles
from schemas.user import User, UserCreate, UserUpdate, UserResponse
from middleware.dependencies import get_current_user
from middleware.audit_logger import log_audit
from auth.hash_password import hash_password
import os

router = APIRouter()


def _normalize_city(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = v.strip()
    return s if s else None

@router.get("/", response_model=List[User])
def list_users(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    ville: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Liste des utilisateurs (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    query = db.query(UserModel)
    
    if organization_id:
        query = query.filter(UserModel.organization_id == organization_id)
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)
    if role:
        query = query.filter(UserModel.role == role)
    if ville:
        query = query.filter(UserModel.ville == ville.strip())
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/me", response_model=User)
def get_me(current_user = Depends(get_current_user)):
    """Obtenir mes propres informations"""
    return current_user


@router.get("/pending", response_model=List[User])
def list_pending_users(
    skip: int = 0,
    limit: int = 100,
    ville: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Liste des utilisateurs en attente d'approbation"""
    user_role = current_user.role if hasattr(current_user, 'role') else None

    if user_role not in ['admin', 'gestionnaire']:
        raise HTTPException(status_code=403, detail="Accès refusé - Admin ou Gestionnaire uniquement")

    query = db.query(UserModel).filter(UserModel.is_active == False)

    # Gestionnaire ne voit que les agents et maintenance en attente
    if user_role == 'gestionnaire':
        manager_city = _normalize_city(getattr(current_user, "ville", None))
        if not manager_city:
            raise HTTPException(status_code=400, detail="Votre compte gestionnaire n'a pas de ville configurée")
        query = query.filter(
            UserModel.role.in_(['agent', 'maintenance']),
            UserModel.ville == manager_city,
        )

    if user_role == 'admin' and ville:
        query = query.filter(UserModel.ville == ville.strip())
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtenir les informations d'un utilisateur"""
    # Un utilisateur peut voir son propre profil, un admin peut voir tous les profils
    if user_id != current_user.id and (not hasattr(current_user, 'role') or current_user.role != 'admin'):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Créer un nouvel utilisateur (admin et gestionnaire peuvent créer selon les règles)"""
    user_role = current_user.role if hasattr(current_user, 'role') else None
    
    # Vérifier les permissions
    if user_role not in ['admin', 'gestionnaire']:
        raise HTTPException(status_code=403, detail="Accès refusé - Admin ou Gestionnaire uniquement")
    
    # Règles d'approbation : Les nouveaux comptes sont inactifs par défaut
    # Admin peut créer tous les types de comptes
    # Gestionnaire peut créer agents et maintenance, mais pas admin ni gestionnaire
    if user_role == 'gestionnaire':
        if user.role in ['admin', 'gestionnaire']:
            raise HTTPException(status_code=403, detail="Un gestionnaire ne peut pas créer de comptes admin ou gestionnaire")

    ville = _normalize_city(user.ville)
    if not ville:
        raise HTTPException(status_code=400, detail="La ville est obligatoire")
    if user_role == "gestionnaire":
        manager_city = _normalize_city(getattr(current_user, "ville", None))
        if not manager_city:
            raise HTTPException(status_code=400, detail="Votre compte gestionnaire n'a pas de ville configurée")
        if ville.lower() != manager_city.lower():
            raise HTTPException(status_code=403, detail="Un gestionnaire ne peut créer que des comptes de sa propre ville")
    
    # Vérifier username unique
    existing = db.query(UserModel).filter(UserModel.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà")
    
    # Vérifier email unique si fourni
    if user.email:
        email_exist = db.query(UserModel).filter(UserModel.email == user.email).first()
        if email_exist:
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    # Nouveaux comptes sont inactifs par défaut (nécessitent approbation)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        ville=ville,
        organization_id=user.organization_id,
        is_active=False  # Inactif par défaut, nécessite approbation
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    log_audit(db, "create", "User", user_id=current_user.id, resource_id=db_user.id, request=request)
    return db_user

@router.post("/{user_id}/approve", response_model=User)
def approve_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Approuver un utilisateur (activer son compte)
    - Admin peut approuver tous les comptes
    - Gestionnaire peut approuver agents et maintenance uniquement
    """
    user_role = current_user.role if hasattr(current_user, 'role') else None
    
    if user_role not in ['admin', 'gestionnaire']:
        raise HTTPException(status_code=403, detail="Accès refusé - Admin ou Gestionnaire uniquement")
    
    user_to_approve = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user_to_approve:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Vérifier les permissions d'approbation
    if user_role == 'gestionnaire':
        # Gestionnaire ne peut approuver que agents et maintenance
        if user_to_approve.role in ['admin', 'gestionnaire']:
            raise HTTPException(
                status_code=403, 
                detail="Un gestionnaire ne peut pas approuver des comptes admin ou gestionnaire"
            )
        manager_city = _normalize_city(getattr(current_user, "ville", None))
        if not manager_city or _normalize_city(user_to_approve.ville) != manager_city:
            raise HTTPException(status_code=403, detail="Un gestionnaire ne peut approuver que les comptes de sa ville")
    
    # Activer le compte
    user_to_approve.is_active = True
    db.commit()
    db.refresh(user_to_approve)
    
    log_audit(
        db, 
        "approve_user", 
        "User", 
        user_id=current_user.id, 
        resource_id=user_id,
        details={"approved_role": user_to_approve.role},
        request=request
    )
    return user_to_approve


@router.post("/{user_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
def reject_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Refuser une demande de compte (suppression définitive — compte encore inactif uniquement).
    - Admin peut refuser tout compte en attente
    - Gestionnaire peut refuser uniquement agents et maintenance en attente
    """
    user_role = current_user.role if hasattr(current_user, "role") else None

    if user_role not in ["admin", "gestionnaire"]:
        raise HTTPException(status_code=403, detail="Accès refusé - Admin ou Gestionnaire uniquement")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas refuser votre propre compte")

    target = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    if target.is_active:
        raise HTTPException(
            status_code=400,
            detail="Seuls les comptes en attente d'approbation (inactifs) peuvent être refusés",
        )

    if user_role == "gestionnaire" and target.role in ["admin", "gestionnaire"]:
        raise HTTPException(
            status_code=403,
            detail="Un gestionnaire ne peut pas refuser des comptes admin ou gestionnaire",
        )
    if user_role == "gestionnaire":
        manager_city = _normalize_city(getattr(current_user, "ville", None))
        if not manager_city or _normalize_city(target.ville) != manager_city:
            raise HTTPException(status_code=403, detail="Un gestionnaire ne peut refuser que les comptes de sa ville")

    rejected_username = target.username
    rejected_role = target.role

    # Nettoyage des lignes liées avant suppression
    db.execute(delete(SessionModel).where(SessionModel.user_id == user_id))
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id))
    db.execute(delete(user_roles).where(user_roles.c.user_id == user_id))

    db.delete(target)
    db.commit()

    log_audit(
        db,
        "reject_user",
        "User",
        user_id=current_user.id,
        resource_id=user_id,
        details={"rejected_username": rejected_username, "rejected_role": rejected_role},
        request=request,
    )
    return None


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Modifier un utilisateur"""
    # Un utilisateur peut modifier son propre profil (sauf is_active), un admin peut modifier tous les profils
    if user_id != current_user.id and (not hasattr(current_user, 'role') or current_user.role != 'admin'):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Un utilisateur non-admin ne peut pas modifier is_active
    if user_id == current_user.id and "is_active" in user_update.model_dump(exclude_unset=True):
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas modifier votre statut actif")
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Vérifier email unique si modifié
    if "email" in update_data and update_data["email"]:
        email_exist = db.query(UserModel).filter(
            UserModel.email == update_data["email"],
            UserModel.id != user_id
        ).first()
        if email_exist:
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    log_audit(db, "update", "User", user_id=current_user.id, resource_id=user_id, request=request)
    return db_user

@router.post("/{user_id}/activate", response_model=User)
def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Activer un utilisateur (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    db_user.is_active = True
    db.commit()
    db.refresh(db_user)
    
    log_audit(db, "activate", "User", user_id=current_user.id, resource_id=user_id, request=request)
    return db_user

@router.post("/{user_id}/deactivate", response_model=User)
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Désactiver un utilisateur (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    
    log_audit(db, "deactivate", "User", user_id=current_user.id, resource_id=user_id, request=request)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Supprimer un utilisateur (soft delete - admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")
    
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Soft delete
    db_user.is_active = False
    db.commit()
    
    log_audit(db, "delete", "User", user_id=current_user.id, resource_id=user_id, request=request)
    return None

@router.post("/{user_id}/avatar")
def upload_avatar(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    request: Request = None
):
    """Upload une photo de profil (utilisateur peut uploader sa propre photo, admin peut uploader pour tous)"""
    if user_id != current_user.id and (not hasattr(current_user, 'role') or current_user.role != 'admin'):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Vérifier le type de fichier
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image")
    
    # Vérifier la taille (max 5MB)
    contents = file.file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="Le fichier ne doit pas dépasser 5MB")
    
    # TODO: Sauvegarder le fichier (MinIO, S3, ou système de fichiers)
    # Pour l'instant, on génère juste un nom de fichier
    import uuid
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    file_name = f"{uuid.uuid4()}.{file_extension}"
    # En production, sauvegarder dans MinIO/S3 et obtenir l'URL
    avatar_url = f"/uploads/avatars/{file_name}"
    
    db_user.avatar_url = avatar_url
    db.commit()
    
    log_audit(db, "avatar_upload", "User", user_id=current_user.id, resource_id=user_id, request=request)
    
    return {"message": "Photo de profil uploadée avec succès", "avatar_url": avatar_url}

@router.get("/{user_id}/stats")
def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Statistiques d'un utilisateur"""
    if user_id != current_user.id and (not hasattr(current_user, 'role') or current_user.role != 'admin'):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # TODO: Calculer les statistiques (nombre de billets vendus, etc.)
    from models.billet import Billet as BilletModel
    
    billets_vendus = db.query(BilletModel).filter(BilletModel.agent_id == user_id).count()
    
    return {
        "user_id": user_id,
        "username": db_user.username,
        "billets_vendus": billets_vendus,
        "last_login": db_user.last_login
    }
