from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Chauffeur(Base):
    __tablename__ = "chauffeurs"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    telephone = Column(String)
    email = Column(String)
    numero_permis = Column(String, unique=True, index=True, nullable=False)
    date_embauche = Column(DateTime, default=datetime.utcnow)
    statut = Column(String, default="actif")  # actif, conge, suspendu
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    bus_assignes = relationship("BusChauffeur", back_populates="chauffeur", lazy="dynamic")
    
    def __repr__(self):
        return f"<Chauffeur {self.prenom} {self.nom}>"
