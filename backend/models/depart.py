from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Time
from database import Base
from datetime import datetime, date

class Depart(Base):
    __tablename__ = "departs"
    
    id = Column(Integer, primary_key=True, index=True)
    ligne_id = Column(Integer, ForeignKey("lignes.id"), nullable=False)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)  # Nouveau
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    chauffeur_id = Column(Integer, ForeignKey("chauffeurs.id"), nullable=False)
    date_depart = Column(DateTime, nullable=False, index=True)
    heure_depart = Column(Time, nullable=False)
    places_disponibles = Column(Integer, nullable=False)
    prix = Column(Float, nullable=False)  # Récupéré automatiquement depuis destination.tarif
    statut = Column(String, default="programme")  # programme, en_cours, termine, annule
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Depart {self.id} - Ligne {self.ligne_id} - {self.date_depart}>"
