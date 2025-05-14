from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Ping(Base):
    __tablename__ = "pings"
    id = Column(Integer, primary_key=True)
    bus_id = Column(Integer)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
