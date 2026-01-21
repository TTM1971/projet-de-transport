from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class Destination(Base):
    __tablename__ = "destinations"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, unique=True, index=True, nullable=False)
    ville = Column(String)
    adresse = Column(String)
    tarif = Column(Float, nullable=False)
    duree_estimee_minutes = Column(Integer)
    description = Column(String)
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Destination {self.nom}>"
