from fastapi import APIRouter, Depends, HTTPException
from schemas.billet import Billet, BilletCreate
from typing import List

router = APIRouter()

# Exemple de données fictives (à remplacer par DB)
billets_db = []

@router.get("/", response_model=List[Billet])
def list_billets():
    return billets_db

@router.post("/", response_model=Billet)
def create_billet(billet: BilletCreate):
    new_billet = billet.dict()
    new_billet["id"] = len(billets_db) + 1
    billets_db.append(new_billet)
    return new_billet
