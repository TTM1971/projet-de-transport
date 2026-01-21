from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LigneCreate(BaseModel):
    numero: str
    nom: str
    point_depart: str
    point_arrivee: str
    distance_km: Optional[float] = None
    duree_minutes: Optional[int] = None
    tarif: Optional[float] = None
    statut: str = "active"

class LigneUpdate(BaseModel):
    nom: Optional[str] = None
    point_depart: Optional[str] = None
    point_arrivee: Optional[str] = None
    distance_km: Optional[float] = None
    duree_minutes: Optional[int] = None
    tarif: Optional[float] = None
    statut: Optional[str] = None

class Ligne(LigneCreate):
    id: int
    date_creation: datetime
    
    class Config:
        from_attributes = True
