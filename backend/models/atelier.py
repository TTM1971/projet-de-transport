from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Atelier(Base):
    __tablename__ = "ateliers"
    id = Column(Integer, primary_key=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    technicien_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # ID du technicien
    date_entree = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_sortie = Column(DateTime, nullable=True)
    type_panne = Column(String)  # freinage, pneus, moteur, électrique, etc.
    gravite = Column(String)  # mineure, moyenne, majeure, critique
    description = Column(String)
    pieces_remplacees = Column(String)  # Liste des pièces changées
    cout_intervention = Column(Float)  # Coût en EUR
    statut = Column(String, default="en_attente")  # en_attente, en_cours, terminee, annulee
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    bus = relationship("Bus", back_populates="interventions")
    
    def __repr__(self):
        return f"<Atelier {self.id} - Bus {self.bus_id} - {self.type_panne}>"