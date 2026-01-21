from pydantic import BaseModel
from typing import Optional

class ParametreBase(BaseModel):
    cle: str
    valeur: str
    type: str  # string, integer, float, boolean, json
    description: Optional[str] = None
    categorie: Optional[str] = None
    is_modifiable: bool = True

class ParametreCreate(ParametreBase):
    pass

class ParametreUpdate(BaseModel):
    valeur: Optional[str] = None
    description: Optional[str] = None
    is_modifiable: Optional[bool] = None

class Parametre(ParametreBase):
    id: int
    
    class Config:
        from_attributes = True
