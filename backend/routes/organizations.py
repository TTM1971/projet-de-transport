from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.organization import Organization as OrganizationModel
from schemas.organization import Organization, OrganizationCreate, OrganizationUpdate
from middleware.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[Organization])
def list_organizations(
    skip: int = 0, 
    limit: int = 100, 
    type: str = None,
    db: Session = Depends(get_db)
):
    """Liste toutes les organisations"""
    query = db.query(OrganizationModel)
    if type:
        query = query.filter(OrganizationModel.type == type)
    organizations = query.offset(skip).limit(limit).all()
    return organizations

@router.get("/tree", response_model=List[Organization])
def get_organizations_tree(db: Session = Depends(get_db)):
    """Obtenir l'arbre hiérarchique des organisations"""
    # Retourner uniquement les organisations racine (sans parent)
    root_orgs = db.query(OrganizationModel).filter(OrganizationModel.parent_id == None).all()
    return root_orgs

@router.get("/{org_id}", response_model=Organization)
def get_organization(org_id: int, db: Session = Depends(get_db)):
    """Détails d'une organisation"""
    org = db.query(OrganizationModel).filter(OrganizationModel.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    return org

@router.post("/", response_model=Organization, status_code=status.HTTP_201_CREATED)
def create_organization(
    organization: OrganizationCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Créer une nouvelle organisation (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Vérifier que le parent existe si spécifié
    if organization.parent_id:
        parent = db.query(OrganizationModel).filter(OrganizationModel.id == organization.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Organisation parente non trouvée")
    
    db_org = OrganizationModel(**organization.model_dump())
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org

@router.put("/{org_id}", response_model=Organization)
def update_organization(
    org_id: int,
    org_update: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Modifier une organisation (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_org = db.query(OrganizationModel).filter(OrganizationModel.id == org_id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    update_data = org_update.model_dump(exclude_unset=True)
    
    # Vérifier que le parent existe si modifié
    if "parent_id" in update_data and update_data["parent_id"]:
        parent = db.query(OrganizationModel).filter(OrganizationModel.id == update_data["parent_id"]).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Organisation parente non trouvée")
        # Éviter qu'une organisation soit son propre parent
        if update_data["parent_id"] == org_id:
            raise HTTPException(status_code=400, detail="Une organisation ne peut pas être son propre parent")
    
    for field, value in update_data.items():
        setattr(db_org, field, value)
    
    db.commit()
    db.refresh(db_org)
    return db_org

@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Supprimer une organisation (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_org = db.query(OrganizationModel).filter(OrganizationModel.id == org_id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    # Désactiver au lieu de supprimer (soft delete)
    db_org.is_active = False
    db.commit()
    return None

@router.get("/{org_id}/users", response_model=List[dict])
def get_organization_users(org_id: int, db: Session = Depends(get_db)):
    """Liste des utilisateurs d'une organisation"""
    org = db.query(OrganizationModel).filter(OrganizationModel.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    return [{"id": u.id, "username": u.username, "email": u.email} for u in org.users]

@router.get("/{org_id}/children", response_model=List[Organization])
def get_organization_children(org_id: int, db: Session = Depends(get_db)):
    """Liste des organisations enfants"""
    org = db.query(OrganizationModel).filter(OrganizationModel.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    
    return org.children
