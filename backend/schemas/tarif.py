from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from typing import Literal

class TarifBase(BaseModel):
    destination_id: int
    type_passager: Literal["adulte", "enfant", "senior", "etudiant"]
    montant: float
    date_debut: datetime
    date_fin: Optional[datetime] = None

class TarifCreate(TarifBase):
    pass

class TarifUpdate(BaseModel):
    destination_id: Optional[int] = None
    type_passager: Optional[Literal["adulte", "enfant", "senior", "etudiant"]] = None
    montant: Optional[float] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    is_active: Optional[bool] = None

class Tarif(TarifBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
