from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from database import Base
from datetime import datetime

class Tarif(Base):
    __tablename__ = "tarifs"
    
    id = Column(Integer, primary_key=True, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False, index=True)
    type_passager = Column(String, nullable=False, index=True)  # adulte, enfant, senior, etudiant
    montant = Column(Float, nullable=False)
    date_debut = Column(DateTime, nullable=False)
    date_fin = Column(DateTime, nullable=True)  # NULL = pas de date de fin
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Tarif {self.type_passager} -> {self.montant}€>"
