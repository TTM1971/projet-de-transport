"""Espace chauffeur : planning personnel, statistiques de trajets."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.depart import Depart as DepartModel
from models.ligne import Ligne as LigneModel
from models.destination import Destination as DestinationModel
from models.billet import Billet as BilletModel
from models.chauffeur import Chauffeur as ChauffeurModel
from middleware.dependencies import get_current_chauffeur_profile

router = APIRouter()


@router.get("/me")
def chauffeur_me(
    chauffeur: ChauffeurModel = Depends(get_current_chauffeur_profile),
):
    return {
        "id": chauffeur.id,
        "nom": chauffeur.nom,
        "prenom": chauffeur.prenom,
        "telephone": chauffeur.telephone,
        "statut": chauffeur.statut,
    }


@router.get("/me/dashboard")
def chauffeur_dashboard(
    db: Session = Depends(get_db),
    chauffeur: ChauffeurModel = Depends(get_current_chauffeur_profile),
):
    today = date.today()
    trajets_termines = (
        db.query(func.count(DepartModel.id))
        .filter(
            DepartModel.chauffeur_id == chauffeur.id,
            DepartModel.statut == "termine",
        )
        .scalar()
        or 0
    )
    a_venir = (
        db.query(func.count(DepartModel.id))
        .filter(
            DepartModel.chauffeur_id == chauffeur.id,
            DepartModel.statut.in_(["programme", "en_cours"]),
            func.date(DepartModel.date_depart) >= today,
        )
        .scalar()
        or 0
    )
    billets_total = (
        db.query(func.count(BilletModel.id))
        .join(DepartModel, BilletModel.depart_id == DepartModel.id)
        .filter(
            DepartModel.chauffeur_id == chauffeur.id,
            DepartModel.statut == "termine",
        )
        .scalar()
        or 0
    )

    return {
        "chauffeur_id": chauffeur.id,
        "trajets_effectues": int(trajets_termines),
        "trajets_a_venir": int(a_venir),
        "passagers_transportes_estime": int(billets_total),
    }


def _enrich_depart(db: Session, d: DepartModel) -> dict:
    ligne = db.query(LigneModel).filter(LigneModel.id == d.ligne_id).first()
    dest = db.query(DestinationModel).filter(DestinationModel.id == d.destination_id).first()
    nb_billets = db.query(func.count(BilletModel.id)).filter(BilletModel.depart_id == d.id).scalar() or 0
    h = d.heure_depart
    heure_str = f"{h.hour:02d}:{h.minute:02d}" if h else ""
    return {
        "id": d.id,
        "ligne_id": d.ligne_id,
        "ligne_nom": ligne.nom if ligne else None,
        "destination_id": d.destination_id,
        "destination_nom": dest.nom if dest else None,
        "date": d.date_depart.date().isoformat() if d.date_depart else None,
        "heure": heure_str,
        "statut": d.statut,
        "places_disponibles": d.places_disponibles,
        "prix": d.prix,
        "nb_billets": int(nb_billets),
    }


@router.get("/me/departs")
def chauffeur_mes_departs(
    db: Session = Depends(get_db),
    chauffeur: ChauffeurModel = Depends(get_current_chauffeur_profile),
    futures_seulement: bool = True,
):
    q = db.query(DepartModel).filter(DepartModel.chauffeur_id == chauffeur.id)
    if futures_seulement:
        today = date.today()
        q = q.filter(
            DepartModel.statut.in_(["programme", "en_cours"]),
            func.date(DepartModel.date_depart) >= today,
        )
    departs = q.order_by(DepartModel.date_depart, DepartModel.heure_depart).all()
    return {"departs": [_enrich_depart(db, d) for d in departs]}


@router.get("/me/historique")
def chauffeur_historique(
    db: Session = Depends(get_db),
    chauffeur: ChauffeurModel = Depends(get_current_chauffeur_profile),
    limit: int = 100,
):
    departs = (
        db.query(DepartModel)
        .filter(
            DepartModel.chauffeur_id == chauffeur.id,
            DepartModel.statut == "termine",
        )
        .order_by(DepartModel.date_depart.desc())
        .limit(limit)
        .all()
    )
    return {"departs": [_enrich_depart(db, d) for d in departs]}
