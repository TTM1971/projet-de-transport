from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.role import Role as RoleModel
from models.permission import Permission as PermissionModel
from models.user_role import user_roles
from models.role_permission import role_permissions
from schemas.role import Role, RoleCreate, RoleUpdate, Permission, PermissionCreate, RoleWithPermissions
from middleware.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[Role])
def list_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Liste tous les rôles"""
    roles = db.query(RoleModel).offset(skip).limit(limit).all()
    return roles

@router.get("/{role_id}", response_model=RoleWithPermissions)
def get_role(role_id: int, db: Session = Depends(get_db)):
    """Détails d'un rôle avec ses permissions"""
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rôle non trouvé")
    return role

@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
def create_role(role: RoleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Créer un nouveau rôle (admin uniquement)"""
    # Vérifier que l'utilisateur est admin
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    existing = db.query(RoleModel).filter(RoleModel.name == role.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce rôle existe déjà")
    
    db_role = RoleModel(**role.model_dump())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.put("/{role_id}", response_model=Role)
def update_role(role_id: int, role_update: RoleUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Modifier un rôle (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Rôle non trouvé")
    
    if db_role.is_system:
        raise HTTPException(status_code=400, detail="Les rôles système ne peuvent pas être modifiés")
    
    update_data = role_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_role, field, value)
    
    db.commit()
    db.refresh(db_role)
    return db_role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Supprimer un rôle (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Rôle non trouvé")
    
    if db_role.is_system:
        raise HTTPException(status_code=400, detail="Les rôles système ne peuvent pas être supprimés")
    
    db.delete(db_role)
    db.commit()
    return None

@router.get("/{role_id}/permissions", response_model=List[Permission])
def get_role_permissions(role_id: int, db: Session = Depends(get_db)):
    """Liste des permissions d'un rôle"""
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rôle non trouvé")
    return role.permissions

@router.post("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_permission_to_role(role_id: int, permission_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Assigner une permission à un rôle"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    permission = db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()
    
    if not role or not permission:
        raise HTTPException(status_code=404, detail="Rôle ou permission non trouvé")
    
    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()
    
    return None

@router.delete("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_permission_from_role(role_id: int, permission_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Retirer une permission d'un rôle"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    permission = db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()
    
    if not role or not permission:
        raise HTTPException(status_code=404, detail="Rôle ou permission non trouvé")
    
    if permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()
    
    return None

@router.get("/permissions/", response_model=List[Permission])
def list_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Liste toutes les permissions"""
    permissions = db.query(PermissionModel).offset(skip).limit(limit).all()
    return permissions

@router.post("/permissions/", response_model=Permission, status_code=status.HTTP_201_CREATED)
def create_permission(permission: PermissionCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Créer une nouvelle permission"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    existing = db.query(PermissionModel).filter(
        PermissionModel.resource == permission.resource,
        PermissionModel.action == permission.action
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Cette permission existe déjà")
    
    db_permission = PermissionModel(**permission.model_dump())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission
