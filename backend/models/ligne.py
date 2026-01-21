from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class Ligne(Base):
    __tablename__ = "lignes"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True, index=True, nullable=False)
    nom = Column(String, nullable=False)
    point_depart = Column(String, nullable=False)
    point_arrivee = Column(String, nullable=False)
    distance_km = Column(Float)
    duree_minutes = Column(Integer)
    tarif = Column(Float)
    statut = Column(String, default="active")  # active, inactive
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Ligne {self.numero}: {self.point_depart} -> {self.point_arrivee}>"
