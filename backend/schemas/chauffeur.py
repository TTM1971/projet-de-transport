from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChauffeurCreate(BaseModel):
    nom: str
    prenom: str
    telephone: Optional[str] = None
    email: Optional[str] = None
    numero_permis: str
    date_embauche: Optional[datetime] = None
    statut: str = "actif"

class ChauffeurUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    numero_permis: Optional[str] = None
    statut: Optional[str] = None

class Chauffeur(ChauffeurCreate):
    id: int
    date_creation: datetime
    
    class Config:
        from_attributes = True
