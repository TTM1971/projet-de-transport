from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.chauffeur import Chauffeur as ChauffeurModel
from schemas.chauffeur import ChauffeurCreate, ChauffeurUpdate, Chauffeur as ChauffeurSchema
from middleware.dependencies import get_current_user, require_gestionnaire_or_admin

router = APIRouter()

@router.get("/", response_model=List[ChauffeurSchema])
def list_chauffeurs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Liste des chauffeurs - Gestionnaires et Admins peuvent consulter pour assigner les créneaux"""
    chauffeurs = db.query(ChauffeurModel).offset(skip).limit(limit).all()
    return chauffeurs

@router.get("/{chauffeur_id}", response_model=ChauffeurSchema)
def get_chauffeur(chauffeur_id: int, db: Session = Depends(get_db)):
    """Détails d'un chauffeur - Gestionnaires et Admins peuvent consulter pour suivi des performances"""
    chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not chauffeur:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    return chauffeur

@router.post("/", response_model=ChauffeurSchema)
def create_chauffeur(chauffeur: ChauffeurCreate, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    # Validation du numéro de permis
    if not chauffeur.numero_permis or not chauffeur.numero_permis.strip():
        raise HTTPException(status_code=400, detail="Le numéro de permis est obligatoire")
    
    # Vérifier si le numéro existe déjà
    existing = db.query(ChauffeurModel).filter(ChauffeurModel.numero_permis == chauffeur.numero_permis.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de permis existe déjà")
    
    # Validation du nom et prénom
    if not chauffeur.nom or not chauffeur.nom.strip():
        raise HTTPException(status_code=400, detail="Le nom est obligatoire")
    
    if not chauffeur.prenom or not chauffeur.prenom.strip():
        raise HTTPException(status_code=400, detail="Le prénom est obligatoire")
    
    # Validation de la date de naissance si fournie
    if chauffeur.date_naissance:
        from datetime import datetime
        if chauffeur.date_naissance > datetime.now().date():
            raise HTTPException(status_code=400, detail="La date de naissance ne peut pas être dans le futur")
    
    chauffeur_data = chauffeur.model_dump()
    chauffeur_data['numero_permis'] = chauffeur_data['numero_permis'].strip()
    chauffeur_data['nom'] = chauffeur_data['nom'].strip()
    chauffeur_data['prenom'] = chauffeur_data['prenom'].strip()
    
    db_chauffeur = ChauffeurModel(**chauffeur_data)
    db.add(db_chauffeur)
    db.commit()
    db.refresh(db_chauffeur)
    return db_chauffeur

@router.put("/{chauffeur_id}", response_model=ChauffeurSchema)
def update_chauffeur(chauffeur_id: int, chauffeur_update: ChauffeurUpdate, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    db_chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not db_chauffeur:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    update_data = chauffeur_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_chauffeur, field, value)
    
    db.commit()
    db.refresh(db_chauffeur)
    return db_chauffeur

@router.delete("/{chauffeur_id}")
def delete_chauffeur(chauffeur_id: int, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    db_chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not db_chauffeur:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    db.delete(db_chauffeur)
    db.commit()
    return {"message": "Chauffeur supprimé avec succès"}
