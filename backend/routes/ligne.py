from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.ligne import Ligne as LigneModel
from schemas.ligne import LigneCreate, LigneUpdate, Ligne as LigneSchema
from middleware.dependencies import get_current_user, require_gestionnaire_or_admin

router = APIRouter()

@router.get("/", response_model=List[LigneSchema])
def list_lignes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Liste des lignes - accessible à tous pour consultation"""
    lignes = db.query(LigneModel).offset(skip).limit(limit).all()
    return lignes

@router.get("/{ligne_id}", response_model=LigneSchema)
def get_ligne(ligne_id: int, db: Session = Depends(get_db)):
    """Détails d'une ligne - accessible à tous pour consultation"""
    ligne = db.query(LigneModel).filter(LigneModel.id == ligne_id).first()
    if not ligne:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    return ligne

@router.post("/", response_model=LigneSchema)
def create_ligne(ligne: LigneCreate, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    # Validation du numéro de ligne
    if not ligne.numero or not str(ligne.numero).strip():
        raise HTTPException(status_code=400, detail="Le numéro de ligne est obligatoire")
    
    # Vérifier si le numéro existe déjà
    existing = db.query(LigneModel).filter(LigneModel.numero == ligne.numero).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de ligne existe déjà")
    
    # Validation des points de départ et d'arrivée
    if not ligne.point_depart or not ligne.point_depart.strip():
        raise HTTPException(status_code=400, detail="Le point de départ est obligatoire")
    
    if not ligne.point_arrivee or not ligne.point_arrivee.strip():
        raise HTTPException(status_code=400, detail="Le point d'arrivée est obligatoire")
    
    # Validation du statut
    valid_status = ['active', 'inactive', 'suspendue']
    if ligne.statut and ligne.statut not in valid_status:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Statuts acceptés: {', '.join(valid_status)}")
    
    ligne_data = ligne.model_dump()
    ligne_data['point_depart'] = ligne_data['point_depart'].strip()
    ligne_data['point_arrivee'] = ligne_data['point_arrivee'].strip()
    
    db_ligne = LigneModel(**ligne_data)
    db.add(db_ligne)
    db.commit()
    db.refresh(db_ligne)
    return db_ligne

@router.put("/{ligne_id}", response_model=LigneSchema)
def update_ligne(ligne_id: int, ligne_update: LigneUpdate, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    db_ligne = db.query(LigneModel).filter(LigneModel.id == ligne_id).first()
    if not db_ligne:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    
    update_data = ligne_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ligne, field, value)
    
    db.commit()
    db.refresh(db_ligne)
    return db_ligne

@router.delete("/{ligne_id}")
def delete_ligne(ligne_id: int, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    db_ligne = db.query(LigneModel).filter(LigneModel.id == ligne_id).first()
    if not db_ligne:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    
    db.delete(db_ligne)
    db.commit()
    return {"message": "Ligne supprimée avec succès"}
