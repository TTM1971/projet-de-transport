"""
Modèle pour l'assignation de chauffeurs aux bus
Gère l'alternance jour/nuit et les congés
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class BusChauffeur(Base):
    __tablename__ = "bus_chauffeurs"
    
    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False, index=True)
    chauffeur_id = Column(Integer, ForeignKey("chauffeurs.id"), nullable=False, index=True)
    type_affectation = Column(String, nullable=False)  # "jour" ou "nuit"
    date_debut = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_fin = Column(DateTime, nullable=True)  # Null si toujours actif
    is_actif = Column(Boolean, default=True, index=True)
    notes = Column(String)  # Notes sur l'assignation
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    bus = relationship("Bus", back_populates="chauffeurs_assignes")
    chauffeur = relationship("Chauffeur", back_populates="bus_assignes")
    
    def __repr__(self):
        return f"<BusChauffeur Bus {self.bus_id} - Chauffeur {self.chauffeur_id} - {self.type_affectation}>"
