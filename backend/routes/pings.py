from fastapi import APIRouter, Depends
from schemas.ping import PingCreate
from models.pings import Ping
from sqlalchemy.orm import Session
from database import get_db
from typing import List

router = APIRouter()

@router.get("/", response_model=List[dict])
def list_pings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    pings = db.query(Ping).order_by(Ping.timestamp.desc()).offset(skip).limit(limit).all()
    return [{"id": p.id, "bus_id": p.bus_id, "status": p.status, "timestamp": p.timestamp} for p in pings]

@router.post("/")
def enregistrer_ping(ping_data: PingCreate, db: Session = Depends(get_db)):
    db_ping = Ping(**ping_data.model_dump())
    db.add(db_ping)
    db.commit()
    db.refresh(db_ping)
    return {"message": "Ping enregistré", "id": db_ping.id}
