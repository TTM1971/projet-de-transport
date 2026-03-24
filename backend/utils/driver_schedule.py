"""
Détection de conflits d'horaires pour les chauffeurs (chevauchement de trajets).
Durée de blocage d'un trajet = buffer ML ou défaut (minutes).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, time
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from models.depart import Depart as DepartModel

# Durée minimale entre deux départs pour le même chauffeur (blocage calendrier)
DEFAULT_TRIP_BLOCK_MINUTES = int(os.getenv("DRIVER_TRIP_BLOCK_MINUTES", "90"))


def depart_start_end(depart: DepartModel, block_minutes: Optional[int] = None) -> Tuple[datetime, datetime]:
    """Fenêtre [début, fin) occupée par le départ pour ce chauffeur."""
    m = block_minutes if block_minutes is not None else DEFAULT_TRIP_BLOCK_MINUTES
    if depart.date_depart is None or depart.heure_depart is None:
        raise ValueError("date_depart / heure_depart manquants")
    d = depart.date_depart.date() if isinstance(depart.date_depart, datetime) else depart.date_depart
    start = datetime.combine(d, depart.heure_depart)
    end = start + timedelta(minutes=m)
    return start, end


def intervals_overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def find_conflicting_departs(
    db: Session,
    chauffeur_id: int,
    window_start: datetime,
    window_end: datetime,
    exclude_depart_id: Optional[int] = None,
    block_minutes: Optional[int] = None,
) -> list[DepartModel]:
    """Retourne les départs du chauffeur qui chevauchent [window_start, window_end)."""
    m = block_minutes if block_minutes is not None else DEFAULT_TRIP_BLOCK_MINUTES
    q = db.query(DepartModel).filter(
        DepartModel.chauffeur_id == chauffeur_id,
        DepartModel.statut != "annule",
    )
    if exclude_depart_id is not None:
        q = q.filter(DepartModel.id != exclude_depart_id)
    candidates = q.all()
    conflicts = []
    for d in candidates:
        try:
            ds, de = depart_start_end(d, m)
        except Exception:
            continue
        if intervals_overlap(window_start, window_end, ds, de):
            conflicts.append(d)
    return conflicts


def assert_no_driver_conflict(
    db: Session,
    chauffeur_id: int,
    window_start: datetime,
    window_end: datetime,
    exclude_depart_id: Optional[int] = None,
    block_minutes: Optional[int] = None,
) -> None:
    from fastapi import HTTPException

    conflicts = find_conflicting_departs(
        db, chauffeur_id, window_start, window_end, exclude_depart_id, block_minutes
    )
    if conflicts:
        ids = [c.id for c in conflicts[:5]]
        raise HTTPException(
            status_code=409,
            detail=(
                f"Conflit d'horaire : ce chauffeur a déjà un trajet qui chevauche ce créneau "
                f"(départs concernés : {ids}). Ajustez l'heure ou choisissez un autre chauffeur."
            ),
        )


def window_for_depart_fields(
    date_depart: datetime,
    heure_depart: time,
    block_minutes: Optional[int] = None,
) -> Tuple[datetime, datetime]:
    m = block_minutes if block_minutes is not None else DEFAULT_TRIP_BLOCK_MINUTES
    start = datetime.combine(date_depart.date(), heure_depart)
    end = start + timedelta(minutes=m)
    return start, end
