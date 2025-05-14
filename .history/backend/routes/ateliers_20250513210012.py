from fastapi import APIRouter, Depends
from schemas.atelier import AtelierCreate
from models.atelier import Atelier
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()

@router.post("/")
def enregistrer_passage(atelier: AtelierCreate, db: Session = Depends(get_db)):
    db_atelier = Atelier(**atelier.dict())
    db.add(db_atelier)
    db.commit()
    return {"message": "Passage atelier enregistré"}
