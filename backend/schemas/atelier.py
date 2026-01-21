from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AtelierCreate(BaseModel):
    bus_id: int
    technicien_id: Optional[int] = None
    date_entree: Optional[datetime] = None
    date_sortie: Optional[datetime] = None
    type_panne: Optional[str] = None
    gravite: Optional[str] = None
    description: Optional[str] = None
    pieces_remplacees: Optional[str] = None
    cout_intervention: Optional[float] = None
    statut: Optional[str] = "en_attente"

class AtelierUpdate(BaseModel):
    date_sortie: Optional[datetime] = None
    type_panne: Optional[str] = None
    gravite: Optional[str] = None
    description: Optional[str] = None
    pieces_remplacees: Optional[str] = None
    cout_intervention: Optional[float] = None
    statut: Optional[str] = None

class Atelier(AtelierCreate):
    id: int
    date_creation: datetime
    
    class Config:
        from_attributes = True
