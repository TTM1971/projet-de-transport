"""
Routes pour gérer les assignations de chauffeurs aux bus
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from models.bus_chauffeur import BusChauffeur as BusChauffeurModel
from models.bus import Bus as BusModel
from models.chauffeur import Chauffeur as ChauffeurModel
from schemas.bus_chauffeur import BusChauffeurCreate, BusChauffeurUpdate, BusChauffeur as BusChauffeurSchema
from middleware.dependencies import require_admin, require_gestionnaire_or_admin, get_current_user

router = APIRouter()

@router.get("/bus/{bus_id}/chauffeurs", response_model=List[BusChauffeurSchema])
def get_chauffeurs_for_bus(
    bus_id: int,
    actif_only: bool = True,
    db: Session = Depends(get_db)
):
    """Récupère tous les chauffeurs assignés à un bus"""
    bus = db.query(BusModel).filter(BusModel.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus non trouvé")
    
    query = db.query(BusChauffeurModel).filter(BusChauffeurModel.bus_id == bus_id)
    if actif_only:
        query = query.filter(BusChauffeurModel.is_actif == True)
    
    assignations = query.order_by(BusChauffeurModel.type_affectation).all()
    return assignations

@router.get("/chauffeur/{chauffeur_id}/bus", response_model=List[BusChauffeurSchema])
def get_bus_for_chauffeur(
    chauffeur_id: int,
    actif_only: bool = True,
    db: Session = Depends(get_db)
):
    """Récupère tous les bus assignés à un chauffeur"""
    chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not chauffeur:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    query = db.query(BusChauffeurModel).filter(BusChauffeurModel.chauffeur_id == chauffeur_id)
    if actif_only:
        query = query.filter(BusChauffeurModel.is_actif == True)
    
    assignations = query.all()
    return assignations

@router.post("/", response_model=BusChauffeurSchema, status_code=status.HTTP_201_CREATED)
def create_bus_chauffeur_assignation(
    assignation: BusChauffeurCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_gestionnaire_or_admin)
):
    """
    Crée une nouvelle assignation de chauffeur à un bus
    - Par défaut, chaque bus doit avoir 2 chauffeurs (1 jour, 1 nuit)
    - Admin peut assigner plus de 2 chauffeurs
    - Agent/Gestionnaire ne peut assigner que 2 chauffeurs maximum
    """
    # Vérifier que le bus existe
    bus = db.query(BusModel).filter(BusModel.id == assignation.bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus non trouvé")
    
    # Vérifier que le chauffeur existe
    chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == assignation.chauffeur_id).first()
    if not chauffeur:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    # Vérifier que le type d'affectation est valide
    if assignation.type_affectation not in ["jour", "nuit"]:
        raise HTTPException(status_code=400, detail="Type d'affectation doit être 'jour' ou 'nuit'")
    
    # Compter les assignations actives pour ce bus
    existing_assignations = db.query(BusChauffeurModel).filter(
        BusChauffeurModel.bus_id == assignation.bus_id,
        BusChauffeurModel.is_actif == True
    ).all()
    
    user_role = current_user.role if hasattr(current_user, 'role') else None
    
    # Règle : Agent/Gestionnaire ne peut assigner que 2 chauffeurs max (1 jour + 1 nuit)
    # Admin peut assigner plus de 2 chauffeurs si nécessaire
    if user_role != 'admin' and len(existing_assignations) >= 2:
        raise HTTPException(
            status_code=403,
            detail="Un agent ou gestionnaire ne peut assigner que 2 chauffeurs maximum par bus (1 jour + 1 nuit). Seul un administrateur peut assigner plus de chauffeurs."
        )
    
    # Vérifier qu'il n'y a pas déjà un chauffeur actif pour ce type d'affectation sur ce bus
    existing_same_type = db.query(BusChauffeurModel).filter(
        BusChauffeurModel.bus_id == assignation.bus_id,
        BusChauffeurModel.type_affectation == assignation.type_affectation,
        BusChauffeurModel.is_actif == True
    ).first()
    
    # Si l'utilisateur n'est pas admin et qu'il y a déjà un chauffeur pour ce type, refuser
    if existing_same_type and user_role != 'admin':
        raise HTTPException(
            status_code=400,
            detail=f"Un chauffeur est déjà assigné à ce bus en {assignation.type_affectation}. Un agent ou gestionnaire ne peut avoir qu'un seul chauffeur par type d'affectation."
        )
    
    # Vérifier que le chauffeur n'est pas déjà assigné à un autre bus au même type
    other_assignation = db.query(BusChauffeurModel).filter(
        BusChauffeurModel.chauffeur_id == assignation.chauffeur_id,
        BusChauffeurModel.type_affectation == assignation.type_affectation,
        BusChauffeurModel.is_actif == True,
        BusChauffeurModel.bus_id != assignation.bus_id
    ).first()
    
    if other_assignation:
        raise HTTPException(
            status_code=400,
            detail="Ce chauffeur est déjà assigné à un autre bus avec le même type d'affectation."
        )
    
    db_assignation = BusChauffeurModel(
        bus_id=assignation.bus_id,
        chauffeur_id=assignation.chauffeur_id,
        type_affectation=assignation.type_affectation,
        date_debut=assignation.date_debut or datetime.utcnow(),
        date_fin=assignation.date_fin,
        notes=assignation.notes,
        is_actif=True
    )
    db.add(db_assignation)
    db.commit()
    db.refresh(db_assignation)
    return db_assignation

@router.put("/{assignation_id}", response_model=BusChauffeurSchema, dependencies=[Depends(require_gestionnaire_or_admin)])
def update_bus_chauffeur_assignation(
    assignation_id: int,
    assignation_update: BusChauffeurUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour une assignation (par exemple pour la terminer)"""
    db_assignation = db.query(BusChauffeurModel).filter(BusChauffeurModel.id == assignation_id).first()
    if not db_assignation:
        raise HTTPException(status_code=404, detail="Assignation non trouvée")
    
    update_data = assignation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_assignation, field, value)
    
    db.commit()
    db.refresh(db_assignation)
    return db_assignation

@router.delete("/{assignation_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_bus_chauffeur_assignation(
    assignation_id: int,
    db: Session = Depends(get_db)
):
    """Supprime une assignation (Admin uniquement)"""
    db_assignation = db.query(BusChauffeurModel).filter(BusChauffeurModel.id == assignation_id).first()
    if not db_assignation:
        raise HTTPException(status_code=404, detail="Assignation non trouvée")
    
    db.delete(db_assignation)
    db.commit()
    return {"message": "Assignation supprimée avec succès"}
