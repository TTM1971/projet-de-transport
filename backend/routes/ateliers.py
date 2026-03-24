
from fastapi import APIRouter, Depends, HTTPException
from schemas.atelier import AtelierCreate, AtelierUpdate, Atelier as AtelierSchema
from models.atelier import Atelier as AtelierModel
from models.bus import Bus as BusModel
from sqlalchemy.orm import Session
from database import get_db
from typing import List, Optional
from datetime import datetime
from middleware.dependencies import maintenance_or_admin_only, get_current_user

router = APIRouter()

@router.get("/", response_model=List[AtelierSchema])
def list_ateliers(
    skip: int = 0, 
    limit: int = 100,
    bus_id: Optional[int] = None,
    statut: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Liste toutes les interventions de maintenance avec filtres"""
    query = db.query(AtelierModel)
    
    if bus_id:
        query = query.filter(AtelierModel.bus_id == bus_id)
    if statut:
        query = query.filter(AtelierModel.statut == statut)
    
    ateliers = query.order_by(AtelierModel.date_entree.desc()).offset(skip).limit(limit).all()
    return ateliers

@router.get("/{intervention_id}", response_model=AtelierSchema)
def get_intervention(intervention_id: int, db: Session = Depends(get_db)):
    """Détails d'une intervention"""
    intervention = db.query(AtelierModel).filter(AtelierModel.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.post("/", response_model=AtelierSchema, status_code=201)
def enregistrer_intervention(
    atelier_data: AtelierCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(maintenance_or_admin_only)
):
    """Enregistre une nouvelle intervention de maintenance"""
    # Vérifier que le bus existe
    bus = db.query(BusModel).filter(BusModel.id == atelier_data.bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus non trouvé")
    
    # Si technicien_id n'est pas fourni, utiliser l'utilisateur courant
    technicien_id = atelier_data.technicien_id
    if not technicien_id:
        technicien_id = current_user.id
    
    db_atelier = AtelierModel(
        bus_id=atelier_data.bus_id,
        technicien_id=technicien_id,
        date_entree=atelier_data.date_entree or datetime.utcnow(),
        date_sortie=atelier_data.date_sortie,
        type_panne=atelier_data.type_panne,
        gravite=atelier_data.gravite,
        description=atelier_data.description,
        pieces_remplacees=atelier_data.pieces_remplacees,
        cout_intervention=atelier_data.cout_intervention,
        statut=atelier_data.statut or "en_attente"
    )
    db.add(db_atelier)
    
    # Mettre le bus en maintenance si nécessaire
    if bus.statut != "en_maintenance" and atelier_data.statut in ["en_attente", "en_cours"]:
        bus.statut = "en_maintenance"
    
    db.commit()
    db.refresh(db_atelier)
    return db_atelier

@router.put("/{intervention_id}", response_model=AtelierSchema)
def update_intervention(
    intervention_id: int,
    atelier_update: AtelierUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(maintenance_or_admin_only)
):
    """Met à jour une intervention de maintenance"""
    intervention = db.query(AtelierModel).filter(AtelierModel.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    
    update_data = atelier_update.model_dump(exclude_unset=True)
    
    # Si le statut passe à "terminee", mettre à jour la date de sortie si nécessaire
    if update_data.get("statut") == "terminee" and not intervention.date_sortie:
        update_data["date_sortie"] = datetime.utcnow()
    
    # Si le statut passe à "terminee", remettre le bus en service si nécessaire
    if update_data.get("statut") == "terminee":
        bus = db.query(BusModel).filter(BusModel.id == intervention.bus_id).first()
        if bus:
            # Vérifier s'il y a d'autres interventions en cours pour ce bus
            autres_interventions = db.query(AtelierModel).filter(
                AtelierModel.bus_id == bus.id,
                AtelierModel.id != intervention_id,
                AtelierModel.statut.in_(["en_attente", "en_cours"])
            ).count()
            
            if autres_interventions == 0:
                bus.statut = "en_service"
    
    for field, value in update_data.items():
        setattr(intervention, field, value)
    
    db.commit()
    db.refresh(intervention)
    return intervention

@router.delete("/{intervention_id}", status_code=204)
def delete_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(maintenance_or_admin_only)
):
    """Supprime une intervention (maintenance ou admin uniquement)"""
    intervention = db.query(AtelierModel).filter(AtelierModel.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    
    db.delete(intervention)
    db.commit()
    return {"message": "Intervention supprimée avec succès"}
