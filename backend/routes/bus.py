from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from database import get_db
from models.bus import Bus as BusModel
from models.atelier import Atelier as AtelierModel
from models.bus_chauffeur import BusChauffeur as BusChauffeurModel
from models.chauffeur import Chauffeur as ChauffeurModel
from schemas.bus import BusCreate, BusUpdate, Bus as BusSchema
from middleware.dependencies import get_current_user, require_gestionnaire_or_admin

router = APIRouter()

@router.get("/", response_model=List[BusSchema])
def list_buses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Liste des bus - accessible à tous les utilisateurs authentifiés pour consultation"""
    buses = db.query(BusModel).offset(skip).limit(limit).all()
    return buses

@router.get("/{bus_id}", response_model=BusSchema)
def get_bus(bus_id: int, db: Session = Depends(get_db)):
    """Détails d'un bus - accessible à tous les utilisateurs authentifiés"""
    bus = db.query(BusModel).filter(BusModel.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus non trouvé")
    return bus

@router.get("/{bus_id}/interventions")
def get_bus_interventions(bus_id: int, db: Session = Depends(get_db)):
    """Récupère l'historique complet des interventions de maintenance d'un bus"""
    bus = db.query(BusModel).filter(BusModel.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus non trouvé")
    
    interventions = db.query(AtelierModel).filter(
        AtelierModel.bus_id == bus_id
    ).order_by(AtelierModel.date_entree.desc()).all()
    
    return {
        "bus_id": bus_id,
        "bus": {
            "id": bus.id,
            "immatriculation": bus.immatriculation,
            "marque": bus.marque,
            "modele": bus.modele,
            "annee": bus.annee,
            "statut": bus.statut
        },
        "interventions": [
            {
                "id": i.id,
                "date_entree": i.date_entree.isoformat() if i.date_entree else None,
                "date_sortie": i.date_sortie.isoformat() if i.date_sortie else None,
                "type_panne": i.type_panne,
                "gravite": i.gravite,
                "description": i.description,
                "pieces_remplacees": i.pieces_remplacees,
                "cout_intervention": i.cout_intervention,
                "statut": i.statut,
                "technicien_id": i.technicien_id
            }
            for i in interventions
        ],
        "total_interventions": len(interventions)
    }

@router.get("/{bus_id}/chauffeurs")
def get_bus_chauffeurs(bus_id: int, db: Session = Depends(get_db)):
    """Récupère les chauffeurs assignés à un bus (actifs)"""
    bus = db.query(BusModel).filter(BusModel.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus non trouvé")
    
    assignations = db.query(BusChauffeurModel).filter(
        BusChauffeurModel.bus_id == bus_id,
        BusChauffeurModel.is_actif == True
    ).all()
    
    result = []
    for assignation in assignations:
        chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == assignation.chauffeur_id).first()
        result.append({
            "assignation_id": assignation.id,
            "chauffeur": {
                "id": chauffeur.id if chauffeur else None,
                "nom": chauffeur.nom if chauffeur else None,
                "prenom": chauffeur.prenom if chauffeur else None,
                "statut": chauffeur.statut if chauffeur else None,
                "numero_permis": chauffeur.numero_permis if chauffeur else None,
                "telephone": chauffeur.telephone if chauffeur else None
            },
            "type_affectation": assignation.type_affectation,
            "date_debut": assignation.date_debut.isoformat() if assignation.date_debut else None,
            "date_fin": assignation.date_fin.isoformat() if assignation.date_fin else None,
            "notes": assignation.notes
        })
    
    return {
        "bus_id": bus_id,
        "chauffeurs": result,
        "chauffeur_jour": next((c for c in result if c["type_affectation"] == "jour"), None),
        "chauffeur_nuit": next((c for c in result if c["type_affectation"] == "nuit"), None)
    }

@router.post("/", response_model=BusSchema)
def create_bus(bus: BusCreate, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    # Validation de l'immatriculation
    if not bus.immatriculation or not bus.immatriculation.strip():
        raise HTTPException(status_code=400, detail="L'immatriculation est obligatoire")
    
    # Vérifier si l'immatriculation existe déjà
    existing = db.query(BusModel).filter(BusModel.immatriculation == bus.immatriculation.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cette immatriculation existe déjà")
    
    # Validation de la capacité
    if bus.capacite is not None and bus.capacite <= 0:
        raise HTTPException(status_code=400, detail="La capacité doit être supérieure à 0")
    
    # Validation de l'année
    if bus.annee is not None:
        current_year = datetime.now().year
        if bus.annee < 1900 or bus.annee > current_year + 1:
            raise HTTPException(status_code=400, detail=f"L'année doit être entre 1900 et {current_year + 1}")
    
    # Validation du statut
    valid_status = ['disponible', 'en_service', 'en_maintenance', 'hors_service']
    if bus.statut and bus.statut not in valid_status:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Statuts acceptés: {', '.join(valid_status)}")
    
    bus_data = bus.model_dump()
    bus_data['immatriculation'] = bus_data['immatriculation'].strip()
    
    db_bus = BusModel(**bus_data)
    db.add(db_bus)
    db.commit()
    db.refresh(db_bus)
    return db_bus

@router.put("/{bus_id}", response_model=BusSchema)
def update_bus(bus_id: int, bus_update: BusUpdate, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    db_bus = db.query(BusModel).filter(BusModel.id == bus_id).first()
    if not db_bus:
        raise HTTPException(status_code=404, detail="Bus non trouvé")
    
    update_data = bus_update.model_dump(exclude_unset=True)
    
    # Validation de l'immatriculation si modifiée
    if "immatriculation" in update_data:
        if not update_data["immatriculation"] or not update_data["immatriculation"].strip():
            raise HTTPException(status_code=400, detail="L'immatriculation est obligatoire")
        # Vérifier si une autre immatriculation existe déjà
        existing = db.query(BusModel).filter(
            BusModel.immatriculation == update_data["immatriculation"].strip(),
            BusModel.id != bus_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Cette immatriculation existe déjà")
        update_data["immatriculation"] = update_data["immatriculation"].strip()
    
    # Validation de la capacité
    if "capacite" in update_data and update_data["capacite"] is not None:
        if update_data["capacite"] <= 0:
            raise HTTPException(status_code=400, detail="La capacité doit être supérieure à 0")
    
    # Validation de l'année
    if "annee" in update_data and update_data["annee"] is not None:
        current_year = datetime.now().year
        if update_data["annee"] < 1900 or update_data["annee"] > current_year + 1:
            raise HTTPException(status_code=400, detail=f"L'année doit être entre 1900 et {current_year + 1}")
    
    # Validation du statut
    if "statut" in update_data and update_data["statut"]:
        valid_status = ['disponible', 'en_service', 'en_maintenance', 'hors_service']
        if update_data["statut"] not in valid_status:
            raise HTTPException(status_code=400, detail=f"Statut invalide. Statuts acceptés: {', '.join(valid_status)}")
    
    for field, value in update_data.items():
        setattr(db_bus, field, value)
    
    db.commit()
    db.refresh(db_bus)
    return db_bus

@router.delete("/{bus_id}")
def delete_bus(bus_id: int, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    db_bus = db.query(BusModel).filter(BusModel.id == bus_id).first()
    if not db_bus:
        raise HTTPException(status_code=404, detail="Bus non trouvé")
    
    db.delete(db_bus)
    db.commit()
    return {"message": "Bus supprimé avec succès"}
