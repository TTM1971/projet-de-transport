from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None  # Email optionnel pour compatibilité avec utilisateurs existants
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    ville: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: Optional[str] = None  # Rôle par défaut (compatibilité)
    organization_id: Optional[int] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None  # Changé de EmailStr à str temporairement
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    ville: Optional[str] = None
    avatar_url: Optional[str] = None
    organization_id: Optional[int] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None

class User(UserBase):
    id: int
    role: Optional[str] = None  # Rôle par défaut
    avatar_url: Optional[str] = None
    organization_id: Optional[int] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserWithRoles(User):
    roles: List[str] = []  # Liste des noms de rôles

class UserLogin(BaseModel):
    username: str
    password: str

# Alias pour compatibilité
UserResponse = User
