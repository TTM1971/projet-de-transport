from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BusCreate(BaseModel):
    immatriculation: str
    modele: Optional[str] = None
    marque: Optional[str] = None
    capacite: int = 50
    annee: Optional[int] = None
    statut: str = "disponible"
    date_achat: Optional[datetime] = None

class BusUpdate(BaseModel):
    modele: Optional[str] = None
    marque: Optional[str] = None
    capacite: Optional[int] = None
    annee: Optional[int] = None
    statut: Optional[str] = None

class Bus(BusCreate):
    id: int
    date_creation: datetime
    
    class Config:
        from_attributes = True
