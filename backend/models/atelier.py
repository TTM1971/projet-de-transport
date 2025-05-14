from sqlalchemy import Column, Integer, DateTime
from database import Base
from datetime import datetime

class Atelier(Base):
    __tablename__ = "ateliers"
    id = Column(Integer, primary_key=True)
    bus_id = Column(Integer)
    date_entree = Column(DateTime, default=datetime.utcnow)
    date_sortie = Column(DateTime, nullable=True)
