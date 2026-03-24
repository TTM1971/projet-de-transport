import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.parametre import Parametre as ParametreModel
from models.ligne import Ligne as LigneModel
from middleware.dependencies import get_current_user

router = APIRouter()

CANADA_CITIES = [
    "Ottawa",
    "Toronto",
    "Montréal",
    "Québec",
    "Vancouver",
    "Victoria",
    "Calgary",
    "Edmonton",
    "Winnipeg",
    "Halifax",
]


class VilleCreate(BaseModel):
    ville: str


def _normalize_city(v: str) -> str:
    return v.strip()


def _load_active_cities(db: Session) -> List[str]:
    row = db.query(ParametreModel).filter(ParametreModel.cle == "active_cities").first()
    if row:
        try:
            vals = json.loads(row.valeur or "[]")
            if isinstance(vals, list):
                return [str(x).strip() for x in vals if str(x).strip()]
        except Exception:
            pass

    # Bootstrap depuis les lignes existantes
    cities = []
    for l in db.query(LigneModel).all():
        if l.point_depart:
            city = l.point_depart.split(",")[0].strip()
            if city and city not in cities:
                cities.append(city)
    return cities


def _save_active_cities(db: Session, cities: List[str]) -> None:
    uniq = []
    for c in cities:
        c2 = c.strip()
        if c2 and c2 not in uniq:
            uniq.append(c2)
    row = db.query(ParametreModel).filter(ParametreModel.cle == "active_cities").first()
    payload = json.dumps(uniq, ensure_ascii=False)
    if row:
        row.valeur = payload
        row.type = "json"
        row.categorie = "systeme"
        row.description = "Liste des villes actives pour inscription/gestion"
    else:
        row = ParametreModel(
            cle="active_cities",
            valeur=payload,
            type="json",
            categorie="systeme",
            description="Liste des villes actives pour inscription/gestion",
            is_modifiable=True,
        )
        db.add(row)
    db.commit()


@router.get("/")
def list_villes(db: Session = Depends(get_db)):
    active = _load_active_cities(db)
    available = [c for c in CANADA_CITIES if c not in active]
    return {"active": active, "canada_options": CANADA_CITIES, "available_to_add": available}


@router.post("/")
def add_ville(body: VilleCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé - Admin uniquement")

    ville = _normalize_city(body.ville)
    if ville not in CANADA_CITIES:
        raise HTTPException(status_code=400, detail="Ville non autorisée")

    active = _load_active_cities(db)
    if ville in active:
        return {"message": "Ville déjà active", "ville": ville}

    active.append(ville)
    _save_active_cities(db, active)
    return {"message": "Ville ajoutée", "ville": ville, "active": active}

