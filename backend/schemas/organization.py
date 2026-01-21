from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from typing import Literal

class OrganizationBase(BaseModel):
    name: str
    type: Literal["compagnie", "agence", "gare"]
    parent_id: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[Literal["compagnie", "agence", "gare"]] = None
    parent_id: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None

class Organization(OrganizationBase):
    id: int
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    children: List["Organization"] = []
    
    class Config:
        from_attributes = True

# Résoudre la référence circulaire
Organization.model_rebuild()
