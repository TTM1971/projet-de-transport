from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DestinationCreate(BaseModel):
    nom: str
    ville: Optional[str] = None
    adresse: Optional[str] = None
    tarif: float
    duree_estimee_minutes: Optional[int] = None
    description: Optional[str] = None

class DestinationUpdate(BaseModel):
    nom: Optional[str] = None
    ville: Optional[str] = None
    adresse: Optional[str] = None
    tarif: Optional[float] = None
    duree_estimee_minutes: Optional[int] = None
    description: Optional[str] = None

class Destination(DestinationCreate):
    id: int
    date_creation: datetime
    
    class Config:
        from_attributes = True
