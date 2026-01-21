from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Bus(Base):
    __tablename__ = "buses"
    
    id = Column(Integer, primary_key=True, index=True)
    immatriculation = Column(String, unique=True, index=True, nullable=False)
    modele = Column(String)
    marque = Column(String)
    capacite = Column(Integer, default=50)
    annee = Column(Integer)
    statut = Column(String, default="disponible")  # disponible, en_service, en_maintenance, hors_service
    date_achat = Column(DateTime, default=datetime.utcnow)
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    chauffeurs_assignes = relationship("BusChauffeur", back_populates="bus", lazy="dynamic")
    interventions = relationship("Atelier", back_populates="bus", lazy="dynamic")
    
    def __repr__(self):
        return f"<Bus {self.immatriculation}>"
