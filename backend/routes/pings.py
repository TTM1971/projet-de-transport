from fastapi import APIRouter, Depends
from schemas.ping import PingCreate
from models.ping import Ping
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()

@router.post("/")
def enregistrer_ping(ping: PingCreate, db: Session = Depends(get_db)):
    db_ping = Ping(**ping.dict())
    db.add(db_ping)
    db.commit()
    return {"message": "Ping enregistré"}
