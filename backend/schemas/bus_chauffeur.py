from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BusChauffeurCreate(BaseModel):
    bus_id: int
    chauffeur_id: int
    type_affectation: str  # "jour" ou "nuit"
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    notes: Optional[str] = None

class BusChauffeurUpdate(BaseModel):
    date_fin: Optional[datetime] = None
    is_actif: Optional[bool] = None
    notes: Optional[str] = None

class BusChauffeur(BusChauffeurCreate):
    id: int
    is_actif: bool
    date_creation: datetime
    
    class Config:
        from_attributes = True
