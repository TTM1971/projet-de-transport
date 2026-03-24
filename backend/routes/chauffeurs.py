from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, date, time, timedelta
from pydantic import BaseModel, Field

from database import get_db
from models.chauffeur import Chauffeur as ChauffeurModel
from models.user import User as UserModel
from models.depart import Depart as DepartModel
from models.ligne import Ligne as LigneModel
from models.destination import Destination as DestinationModel
from schemas.chauffeur import (
    ChauffeurUpdate,
    Chauffeur as ChauffeurSchema,
    LinkChauffeurUser,
)
from middleware.dependencies import get_current_user, require_gestionnaire_or_admin, require_admin
from middleware.audit_logger import log_audit
from utils.driver_schedule import assert_no_driver_conflict, window_for_depart_fields
from services.driver_schedule_ml import (
    train_model_from_db,
    score_slot_feasibility,
    predict_block_minutes,
)

router = APIRouter()
MANDATORY_BREAK_MINUTES = 180


class AssignDepartBody(BaseModel):
    depart_id: int


class MlSuggestBody(BaseModel):
    ligne_id: int
    date_str: str = Field(..., description="YYYY-MM-DD")


def _normalize_city(v: str | None) -> str | None:
    if v is None:
        return None
    s = v.strip()
    return s.lower() if s else None


def _line_depart_city(line: LigneModel | None) -> str | None:
    if not line or not line.point_depart:
        return None
    # Ex: "Ottawa, ON (Gare centrale)" -> "ottawa"
    return _normalize_city(line.point_depart.split(",")[0])


def _compute_effective_block_minutes(
    db: Session,
    ligne_id: int,
    weekday: int,
    hour_float: float,
) -> int:
    """
    Durée de blocage utilisée pour les conflits :
    - base ML
    - au minimum la durée réelle de la ligne
    """
    ml_block = int(predict_block_minutes(weekday, hour_float, ligne_id))
    ligne = db.query(LigneModel).filter(LigneModel.id == ligne_id).first()
    ligne_minutes = int(ligne.duree_minutes) if ligne and ligne.duree_minutes else 0
    trip_minutes = max(ml_block, ligne_minutes)
    # Ajoute la pause obligatoire entre deux trajets pour empêcher un enchaînement immédiat.
    return trip_minutes + MANDATORY_BREAK_MINUTES


@router.get("/", response_model=List[ChauffeurSchema])
def list_chauffeurs(
    skip: int = 0,
    limit: int = 100,
    ville: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Liste des chauffeurs - Gestionnaires et Admins peuvent consulter pour assigner les créneaux"""
    q = db.query(ChauffeurModel)
    role = getattr(current_user, "role", None)
    if role == "agent":
        city = _normalize_city(getattr(current_user, "ville", None))
        if city:
            q = q.filter(func.lower(ChauffeurModel.ville) == city)
        else:
            q = q.filter(ChauffeurModel.id == -1)
    elif role == "admin" and ville:
        q = q.filter(func.lower(ChauffeurModel.ville) == _normalize_city(ville))
    chauffeurs = q.offset(skip).limit(limit).all()
    return chauffeurs


def _enrich_depart_admin(db: Session, d: DepartModel) -> dict:
    ligne = db.query(LigneModel).filter(LigneModel.id == d.ligne_id).first()
    dest = db.query(DestinationModel).filter(DestinationModel.id == d.destination_id).first()
    h = d.heure_depart
    heure_str = f"{h.hour:02d}:{h.minute:02d}" if h else ""
    return {
        "id": d.id,
        "ligne_id": d.ligne_id,
        "ligne_nom": ligne.nom if ligne else None,
        "destination_id": d.destination_id,
        "destination_nom": dest.nom if dest else None,
        "bus_id": d.bus_id,
        "date": d.date_depart.date().isoformat() if d.date_depart else None,
        "heure": heure_str,
        "statut": d.statut,
        "places_disponibles": d.places_disponibles,
        "prix": d.prix,
    }


@router.get("/{chauffeur_id}/planning/departs")
def list_chauffeur_planning_departs(
    chauffeur_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_gestionnaire_or_admin),
    futures_seulement: bool = False,
):
    """Tous les départs assignés à ce chauffeur (vue admin)."""
    ch = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    q = db.query(DepartModel).filter(DepartModel.chauffeur_id == chauffeur_id)
    if futures_seulement:
        today = date.today()
        q = q.filter(func.date(DepartModel.date_depart) >= today)
    departs = q.order_by(DepartModel.date_depart, DepartModel.heure_depart).all()
    return {"chauffeur": ChauffeurSchema.model_validate(ch), "departs": [_enrich_depart_admin(db, d) for d in departs]}


@router.post("/{chauffeur_id}/planning/assign-depart")
def assign_depart_to_chauffeur(
    chauffeur_id: int,
    body: AssignDepartBody,
    db: Session = Depends(get_db),
    current_user=Depends(require_gestionnaire_or_admin),
):
    """Attribue un départ existant à ce chauffeur (vérifie les conflits d'horaire)."""
    ch = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    if ch.statut not in ("actif",):
        raise HTTPException(status_code=400, detail="Ce chauffeur n'est pas disponible (statut).")

    d = db.query(DepartModel).filter(DepartModel.id == body.depart_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Départ non trouvé")

    ligne = db.query(LigneModel).filter(LigneModel.id == d.ligne_id).first()
    if not ligne:
        raise HTTPException(status_code=404, detail="Ligne du départ introuvable")

    chauffeur_city = _normalize_city(getattr(ch, "ville", None))
    line_city = _line_depart_city(ligne)
    manager_city = _normalize_city(getattr(current_user, "ville", None))

    if not line_city:
        raise HTTPException(status_code=400, detail="Ville de la ligne introuvable. Vérifiez le point de départ.")
    if not chauffeur_city:
        raise HTTPException(status_code=400, detail="Ville du chauffeur non renseignée.")

    # Un chauffeur doit rester sur les trajets de sa ville.
    if chauffeur_city != line_city:
        raise HTTPException(
            status_code=409,
            detail="Conflit de ville : ce chauffeur ne peut être assigné qu'aux trajets de sa ville.",
        )

    # Un gestionnaire ne peut affecter que dans sa ville.
    if getattr(current_user, "role", None) == "gestionnaire":
        if not manager_city:
            raise HTTPException(status_code=400, detail="Votre compte gestionnaire n'a pas de ville configurée")
        if line_city and manager_city != line_city:
            raise HTTPException(status_code=403, detail="Vous ne pouvez assigner que les trajets de votre ville")
        if chauffeur_city and manager_city != chauffeur_city:
            raise HTTPException(status_code=403, detail="Vous ne pouvez assigner que les chauffeurs de votre ville")

    wd = d.date_depart.weekday()
    hr = float(d.heure_depart.hour + d.heure_depart.minute / 60.0)
    block = _compute_effective_block_minutes(db, d.ligne_id, wd, hr)
    ws, we = window_for_depart_fields(d.date_depart, d.heure_depart, block)

    assert_no_driver_conflict(db, chauffeur_id, ws, we, exclude_depart_id=d.id, block_minutes=block)

    d.chauffeur_id = chauffeur_id
    db.commit()
    db.refresh(d)
    log_audit(
        db,
        action="assign_depart_chauffeur",
        resource_type="Depart",
        user_id=getattr(current_user, "id", None),
        resource_id=d.id,
        details={
            "chauffeur_id": chauffeur_id,
            "ligne_id": d.ligne_id,
            "ville_gestionnaire": getattr(current_user, "ville", None),
            "ville_chauffeur": ch.ville,
            "ville_ligne": ligne.point_depart,
        },
    )
    return {"ok": True, "depart": _enrich_depart_admin(db, d)}


@router.delete("/{chauffeur_id}/planning/unassign-depart/{depart_id}")
def unassign_depart_from_chauffeur(
    chauffeur_id: int,
    depart_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_gestionnaire_or_admin),
):
    """Retire un départ d'un chauffeur si le départ est à plus de 2h."""
    ch = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")

    d = db.query(DepartModel).filter(DepartModel.id == depart_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Départ non trouvé")
    if d.chauffeur_id != chauffeur_id:
        raise HTTPException(status_code=409, detail="Ce départ n'est pas assigné à ce chauffeur")

    ligne = db.query(LigneModel).filter(LigneModel.id == d.ligne_id).first()
    if not ligne:
        raise HTTPException(status_code=404, detail="Ligne du départ introuvable")

    chauffeur_city = _normalize_city(getattr(ch, "ville", None))
    line_city = _line_depart_city(ligne)
    manager_city = _normalize_city(getattr(current_user, "ville", None))

    # Un gestionnaire ne peut retirer que dans sa ville.
    if getattr(current_user, "role", None) == "gestionnaire":
        if not manager_city:
            raise HTTPException(status_code=400, detail="Votre compte gestionnaire n'a pas de ville configurée")
        if line_city and manager_city != line_city:
            raise HTTPException(status_code=403, detail="Vous ne pouvez retirer que les trajets de votre ville")
        if chauffeur_city and manager_city != chauffeur_city:
            raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que les chauffeurs de votre ville")

    depart_dt = datetime.combine(d.date_depart.date(), d.heure_depart) if d.date_depart and d.heure_depart else d.date_depart
    if not depart_dt:
        raise HTTPException(status_code=400, detail="Date/heure du départ introuvable")

    cutoff = datetime.now() + timedelta(hours=2)
    if depart_dt <= cutoff:
        raise HTTPException(
            status_code=409,
            detail="Suppression impossible: un trajet assigné ne peut être retiré qu'au moins 2h avant le départ.",
        )

    d.chauffeur_id = None
    db.commit()
    db.refresh(d)
    log_audit(
        db,
        action="unassign_depart_chauffeur",
        resource_type="Depart",
        user_id=getattr(current_user, "id", None),
        resource_id=d.id,
        details={
            "chauffeur_id": chauffeur_id,
            "ligne_id": d.ligne_id,
            "ville_gestionnaire": getattr(current_user, "ville", None),
            "ville_chauffeur": ch.ville,
            "ville_ligne": ligne.point_depart,
        },
    )
    return {"ok": True, "depart": _enrich_depart_admin(db, d)}


@router.post("/{chauffeur_id}/planning/ml/train")
def train_driver_schedule_ml(
    chauffeur_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Entraîne le modèle RandomForest sur l'historique des départs (tous chauffeurs)."""
    ch = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    return train_model_from_db(db)


@router.post("/{chauffeur_id}/planning/ml/suggest-hours")
def suggest_hours_ml(
    chauffeur_id: int,
    body: MlSuggestBody,
    db: Session = Depends(get_db),
    current_user=Depends(require_gestionnaire_or_admin),
):
    """
    Propose des créneaux horaires classés par score ML pour une ligne et une date,
    en excluant ceux qui entreraient en conflit avec le planning actuel du chauffeur.
    """
    ch = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")

    try:
        day = datetime.strptime(body.date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="date_str invalide (YYYY-MM-DD)")

    ligne = db.query(LigneModel).filter(LigneModel.id == body.ligne_id).first()
    if not ligne:
        raise HTTPException(status_code=404, detail="Ligne introuvable")

    if getattr(current_user, "role", None) == "gestionnaire":
        manager_city = _normalize_city(getattr(current_user, "ville", None))
        line_city = _line_depart_city(ligne)
        chauffeur_city = _normalize_city(getattr(ch, "ville", None))
        if not manager_city:
            raise HTTPException(status_code=400, detail="Votre compte gestionnaire n'a pas de ville configurée")
        if line_city and manager_city != line_city:
            raise HTTPException(status_code=403, detail="Vous ne pouvez suggérer que pour les lignes de votre ville")
        if chauffeur_city and manager_city != chauffeur_city:
            raise HTTPException(status_code=403, detail="Vous ne pouvez planifier que les chauffeurs de votre ville")

    wd = day.weekday()
    suggestions = []
    for hour in range(6, 22):
        hr_f = float(hour)
        block = _compute_effective_block_minutes(db, body.ligne_id, wd, hr_f)
        tstart = datetime.combine(day, time(hour, 0))
        tend = tstart + timedelta(minutes=block)
        try:
            assert_no_driver_conflict(
                db, chauffeur_id, tstart, tend, exclude_depart_id=None, block_minutes=block
            )
            conflict = False
        except HTTPException:
            conflict = True
        score = score_slot_feasibility(wd, hr_f, body.ligne_id)
        suggestions.append(
            {
                "heure": f"{hour:02d}:00",
                "score_ml": round(score, 2),
                "blocage_minutes": block,
                "sans_conflit": not conflict,
            }
        )

    suggestions.sort(key=lambda x: (-x["sans_conflit"], -x["score_ml"]))
    return {"chauffeur_id": chauffeur_id, "ligne_id": body.ligne_id, "date": body.date_str, "suggestions": suggestions}


@router.put("/{chauffeur_id}/link-user", response_model=ChauffeurSchema)
def link_chauffeur_to_user(
    chauffeur_id: int,
    body: LinkChauffeurUser,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Lie un utilisateur (rôle chauffeur) à la fiche Chauffeur pour l'espace conducteur."""
    ch = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")

    u = db.query(UserModel).filter(UserModel.id == body.user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if getattr(u, "role", None) != "chauffeur":
        raise HTTPException(status_code=400, detail="L'utilisateur doit avoir le rôle « chauffeur »")

    other = db.query(ChauffeurModel).filter(ChauffeurModel.user_id == body.user_id, ChauffeurModel.id != chauffeur_id).first()
    if other:
        raise HTTPException(status_code=400, detail="Ce compte est déjà lié à un autre chauffeur")

    ch.user_id = body.user_id
    db.commit()
    db.refresh(ch)
    return ch


@router.get("/{chauffeur_id}", response_model=ChauffeurSchema)
def get_chauffeur(chauffeur_id: int, db: Session = Depends(get_db)):
    """Détails d'un chauffeur - Gestionnaires et Admins peuvent consulter pour suivi des performances"""
    chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not chauffeur:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    return chauffeur

@router.post("/")
def create_chauffeur_disabled():
    """La création de conducteurs via l'API est désactivée (provisionnement RH / scripts)."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="La création de fiches conducteur via l'application est désactivée. Utilisez les procédures RH ou les scripts d'intégration (voir documentation).",
    )

@router.put("/{chauffeur_id}", response_model=ChauffeurSchema)
def update_chauffeur(chauffeur_id: int, chauffeur_update: ChauffeurUpdate, db: Session = Depends(get_db), current_user = Depends(require_gestionnaire_or_admin)):
    db_chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not db_chauffeur:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    update_data = chauffeur_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_chauffeur, field, value)
    
    db.commit()
    db.refresh(db_chauffeur)
    return db_chauffeur

@router.delete("/{chauffeur_id}")
def delete_chauffeur(chauffeur_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    db_chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
    if not db_chauffeur:
        raise HTTPException(status_code=404, detail="Chauffeur non trouvé")
    
    db.delete(db_chauffeur)
    db.commit()
    return {"message": "Chauffeur supprimé avec succès"}
