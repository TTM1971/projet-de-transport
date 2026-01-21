from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BilletCreate(BaseModel):
    depart_id: int  # Obligatoire - référence au départ programmé
    bus_id: int
    destination_id: int
    ligne_id: Optional[int] = None
    chauffeur_id: Optional[int] = None  # Peut venir du départ
    siege: Optional[int] = None
    agent_id: int
    mode_paiement: str
    montant: float
    nom_client: Optional[str] = None
    telephone_client: Optional[str] = None

class BilletUpdate(BaseModel):
    statut: Optional[str] = None
    date_utilisation: Optional[datetime] = None

class Billet(BilletCreate):
    id: int
    date_achat: datetime = datetime.now()
    statut: str = "valide"
    code_qr: Optional[str] = None
    date_utilisation: Optional[datetime] = None
    
    class Config:
        from_attributes = True

