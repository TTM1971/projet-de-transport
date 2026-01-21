from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.parametre import Parametre as ParametreModel
from models.tarif import Tarif as TarifModel
from schemas.parametre import Parametre, ParametreCreate, ParametreUpdate
from schemas.tarif import Tarif, TarifCreate, TarifUpdate
from middleware.dependencies import get_current_user

router = APIRouter()

# Routes Paramètres
@router.get("/", response_model=List[Parametre])
def list_parametres(
    categorie: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Liste des paramètres système"""
    query = db.query(ParametreModel)
    if categorie:
        query = query.filter(ParametreModel.categorie == categorie)
    parametres = query.offset(skip).limit(limit).all()
    return parametres

@router.get("/{cle}", response_model=Parametre)
def get_parametre(cle: str, db: Session = Depends(get_db)):
    """Obtenir un paramètre par sa clé"""
    parametre = db.query(ParametreModel).filter(ParametreModel.cle == cle).first()
    if not parametre:
        raise HTTPException(status_code=404, detail="Paramètre non trouvé")
    return parametre

@router.post("/", response_model=Parametre, status_code=status.HTTP_201_CREATED)
def create_parametre(
    parametre: ParametreCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Créer un nouveau paramètre (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    existing = db.query(ParametreModel).filter(ParametreModel.cle == parametre.cle).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce paramètre existe déjà")
    
    db_parametre = ParametreModel(**parametre.model_dump())
    db.add(db_parametre)
    db.commit()
    db.refresh(db_parametre)
    return db_parametre

@router.put("/{cle}", response_model=Parametre)
def update_parametre(
    cle: str,
    parametre_update: ParametreUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Modifier un paramètre (admin uniquement)"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_parametre = db.query(ParametreModel).filter(ParametreModel.cle == cle).first()
    if not db_parametre:
        raise HTTPException(status_code=404, detail="Paramètre non trouvé")
    
    if not db_parametre.is_modifiable:
        raise HTTPException(status_code=400, detail="Ce paramètre n'est pas modifiable")
    
    update_data = parametre_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_parametre, field, value)
    
    db.commit()
    db.refresh(db_parametre)
    return db_parametre

# Routes Tarifs
@router.get("/tarifs/", response_model=List[Tarif])
def list_tarifs(
    destination_id: Optional[int] = None,
    type_passager: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Liste des tarifs"""
    query = db.query(TarifModel)
    if destination_id:
        query = query.filter(TarifModel.destination_id == destination_id)
    if type_passager:
        query = query.filter(TarifModel.type_passager == type_passager)
    if is_active is not None:
        query = query.filter(TarifModel.is_active == is_active)
    tarifs = query.order_by(TarifModel.date_debut.desc()).offset(skip).limit(limit).all()
    return tarifs

@router.post("/tarifs/", response_model=Tarif, status_code=status.HTTP_201_CREATED)
def create_tarif(
    tarif: TarifCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Créer un nouveau tarif (admin/gestionnaire)"""
    if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'gestionnaire']:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_tarif = TarifModel(**tarif.model_dump())
    db.add(db_tarif)
    db.commit()
    db.refresh(db_tarif)
    return db_tarif

@router.put("/tarifs/{tarif_id}", response_model=Tarif)
def update_tarif(
    tarif_id: int,
    tarif_update: TarifUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Modifier un tarif"""
    if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'gestionnaire']:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_tarif = db.query(TarifModel).filter(TarifModel.id == tarif_id).first()
    if not db_tarif:
        raise HTTPException(status_code=404, detail="Tarif non trouvé")
    
    update_data = tarif_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tarif, field, value)
    
    db.commit()
    db.refresh(db_tarif)
    return db_tarif

@router.delete("/tarifs/{tarif_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tarif(
    tarif_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Supprimer un tarif (désactivation)"""
    if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'gestionnaire']:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    db_tarif = db.query(TarifModel).filter(TarifModel.id == tarif_id).first()
    if not db_tarif:
        raise HTTPException(status_code=404, detail="Tarif non trouvé")
    
    # Soft delete
    db_tarif.is_active = False
    db.commit()
    return None
