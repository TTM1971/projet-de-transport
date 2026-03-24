from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from database import get_db
from models.destination import Destination as DestinationModel
from schemas.destination import DestinationCreate, DestinationUpdate, Destination as DestinationSchema
from middleware.dependencies import get_current_user, gestionnaire_or_admin_only

router = APIRouter()


def _normalize_city(v: str | None) -> str | None:
    if v is None:
        return None
    s = v.strip()
    return s.lower() if s else None

@router.get("/", response_model=List[DestinationSchema])
def list_destinations(
    skip: int = 0,
    limit: int = 100,
    ville: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Liste des destinations - accessible à tous pour consultation (agents peuvent consulter pour aider les clients)"""
    q = db.query(DestinationModel)
    role = getattr(current_user, "role", None)
    city = None
    if role in ("agent", "gestionnaire"):
        city = _normalize_city(getattr(current_user, "ville", None))
    elif role == "admin" and ville:
        city = _normalize_city(ville)
    if city:
        q = q.filter(func.lower(DestinationModel.ville) == city)
    elif role in ("agent", "gestionnaire"):
        q = q.filter(DestinationModel.id == -1)
    destinations = q.offset(skip).limit(limit).all()
    return destinations

@router.get("/{dest_id}", response_model=DestinationSchema)
def get_destination(dest_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Détails d'une destination - accessible à tous pour consultation"""
    destination = db.query(DestinationModel).filter(DestinationModel.id == dest_id).first()
    if not destination:
        raise HTTPException(status_code=404, detail="Destination non trouvée")
    role = getattr(current_user, "role", None)
    if role in ("agent", "gestionnaire"):
        city = _normalize_city(getattr(current_user, "ville", None))
        if not city or _normalize_city(destination.ville) != city:
            raise HTTPException(status_code=403, detail="Accès interdit pour cette ville")
    return destination

@router.post("/", response_model=DestinationSchema)
def create_destination(destination: DestinationCreate, db: Session = Depends(get_db), current_user = Depends(gestionnaire_or_admin_only)):
    # Validation du nom
    if not destination.nom or not destination.nom.strip():
        raise HTTPException(status_code=400, detail="Le nom de la destination est obligatoire")
    
    # Vérifier si le nom existe déjà
    existing = db.query(DestinationModel).filter(DestinationModel.nom == destination.nom.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cette destination existe déjà")
    
    # Validation du tarif
    if destination.tarif is None:
        raise HTTPException(status_code=400, detail="Le tarif est obligatoire")
    if destination.tarif < 0:
        raise HTTPException(status_code=400, detail="Le tarif ne peut pas être négatif")
    
    destination_data = destination.model_dump()
    destination_data['nom'] = destination_data['nom'].strip()
    if destination_data.get('ville'):
        destination_data['ville'] = destination_data['ville'].strip()
    if getattr(current_user, "role", None) == "gestionnaire":
        manager_city = _normalize_city(getattr(current_user, "ville", None))
        if not manager_city:
            raise HTTPException(status_code=400, detail="Votre compte gestionnaire n'a pas de ville configurée")
        if _normalize_city(destination_data.get("ville")) != manager_city:
            raise HTTPException(status_code=403, detail="Un gestionnaire ne peut créer que des destinations de sa ville")
    
    db_destination = DestinationModel(**destination_data)
    db.add(db_destination)
    db.commit()
    db.refresh(db_destination)
    return db_destination

@router.put("/{dest_id}", response_model=DestinationSchema)
def update_destination(dest_id: int, dest_update: DestinationUpdate, db: Session = Depends(get_db), current_user = Depends(gestionnaire_or_admin_only)):
    db_destination = db.query(DestinationModel).filter(DestinationModel.id == dest_id).first()
    if not db_destination:
        raise HTTPException(status_code=404, detail="Destination non trouvée")
    if getattr(current_user, "role", None) == "gestionnaire":
        manager_city = _normalize_city(getattr(current_user, "ville", None))
        if not manager_city or _normalize_city(db_destination.ville) != manager_city:
            raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que les destinations de votre ville")
    
    update_data = dest_update.model_dump(exclude_unset=True)
    
    # Validation du nom si modifié
    if "nom" in update_data:
        if not update_data["nom"] or not update_data["nom"].strip():
            raise HTTPException(status_code=400, detail="Le nom de la destination est obligatoire")
        # Vérifier si un autre nom existe déjà
        existing = db.query(DestinationModel).filter(
            DestinationModel.nom == update_data["nom"].strip(),
            DestinationModel.id != dest_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ce nom de destination existe déjà")
        update_data["nom"] = update_data["nom"].strip()
    
    # Validation du tarif
    if "tarif" in update_data and update_data["tarif"] is not None:
        if update_data["tarif"] < 0:
            raise HTTPException(status_code=400, detail="Le tarif ne peut pas être négatif")
    
    if "ville" in update_data and update_data["ville"]:
        update_data["ville"] = update_data["ville"].strip()
    
    for field, value in update_data.items():
        setattr(db_destination, field, value)
    
    db.commit()
    db.refresh(db_destination)
    return db_destination

@router.delete("/{dest_id}")
def delete_destination(dest_id: int, db: Session = Depends(get_db), current_user = Depends(gestionnaire_or_admin_only)):
    db_destination = db.query(DestinationModel).filter(DestinationModel.id == dest_id).first()
    if not db_destination:
        raise HTTPException(status_code=404, detail="Destination non trouvée")
    if getattr(current_user, "role", None) == "gestionnaire":
        manager_city = _normalize_city(getattr(current_user, "ville", None))
        if not manager_city or _normalize_city(db_destination.ville) != manager_city:
            raise HTTPException(status_code=403, detail="Vous ne pouvez supprimer que les destinations de votre ville")
    
    db.delete(db_destination)
    db.commit()
    return {"message": "Destination supprimée avec succès"}
