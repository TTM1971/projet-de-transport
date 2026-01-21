from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from database import Base
from datetime import datetime

class Billet(Base):
    __tablename__ = "billets"
    
    id = Column(Integer, primary_key=True, index=True)
    depart_id = Column(Integer, ForeignKey("departs.id"), nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    ligne_id = Column(Integer, ForeignKey("lignes.id"), nullable=True)
    chauffeur_id = Column(Integer, ForeignKey("chauffeurs.id"), nullable=True)
    siege = Column(Integer)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mode_paiement = Column(String, nullable=False)  # espece, carte, mobile
    montant = Column(Float, nullable=False)
    date_achat = Column(DateTime, default=datetime.utcnow)
    statut = Column(String, default="valide")  # valide, utilise, annule, rembourse
    code_qr = Column(String, unique=True, index=True)
    date_utilisation = Column(DateTime, nullable=True)
    # Informations client
    nom_client = Column(String, nullable=True)
    telephone_client = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Billet {self.id} - Bus {self.bus_id}>"
