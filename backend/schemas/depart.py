from pydantic import BaseModel, field_serializer, model_validator
from datetime import datetime, date, time
from typing import Optional, Any

class DepartCreate(BaseModel):
    ligne_id: int
    destination_id: int  # Nouveau - le prix sera récupéré automatiquement depuis la destination
    bus_id: int
    chauffeur_id: Optional[int] = None  # Optionnel - sera assigné automatiquement si non spécifié
    date_depart: datetime
    heure_depart: str  # Format "HH:MM"
    places_disponibles: int
    statut: str = "programme"

class DepartUpdate(BaseModel):
    ligne_id: Optional[int] = None
    destination_id: Optional[int] = None  # Si changé, le prix sera mis à jour automatiquement
    bus_id: Optional[int] = None
    chauffeur_id: Optional[int] = None
    date_depart: Optional[datetime] = None
    heure_depart: Optional[str] = None
    places_disponibles: Optional[int] = None
    statut: Optional[str] = None

class Depart(BaseModel):
    id: int
    ligne_id: int
    destination_id: int
    bus_id: int
    chauffeur_id: int
    date_depart: datetime
    heure_depart: str  # Sera sérialisé depuis datetime.time
    places_disponibles: int
    prix: float  # Prix récupéré automatiquement depuis la destination
    statut: str
    date_creation: datetime
    
    @model_validator(mode='before')
    @classmethod
    def convert_heure_depart(cls, data: Any) -> Any:
        """Convertit datetime.time en string HH:MM avant validation"""
        if isinstance(data, dict):
            heure_depart = data.get('heure_depart')
            if isinstance(heure_depart, time):
                data['heure_depart'] = heure_depart.strftime("%H:%M")
        elif hasattr(data, 'heure_depart'):
            heure_depart = data.heure_depart
            if isinstance(heure_depart, time):
                # Créer un dict temporaire pour la conversion
                if not isinstance(data, dict):
                    data_dict = {
                        'id': data.id,
                        'ligne_id': data.ligne_id,
                        'destination_id': data.destination_id,
                        'bus_id': data.bus_id,
                        'chauffeur_id': data.chauffeur_id,
                        'date_depart': data.date_depart,
                        'heure_depart': heure_depart.strftime("%H:%M"),
                        'places_disponibles': data.places_disponibles,
                        'prix': data.prix,
                        'statut': data.statut,
                        'date_creation': data.date_creation
                    }
                    return data_dict
        return data
    
    class Config:
        from_attributes = True
