"""
Planification du personnel de guichet (agents, gestionnaires) et vue agrégée des horaires.
- Admin : agents, chauffeurs (trajets), gestionnaires.
- Gestionnaire : agents et chauffeurs uniquement.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.user import User as UserModel
from models.chauffeur import Chauffeur as ChauffeurModel
from models.staff_shift import StaffShift as StaffShiftModel
from schemas.staff_shift import StaffShiftCreate, StaffShiftUpdate, StaffShiftOut
from middleware.dependencies import get_current_user
from middleware.audit_logger import log_audit
from constants.canada_labour import (
    DEFAULT_TIMEZONE,
    MAX_SHIFT_HOURS,
    HOURS_BEFORE_BREAK_RECOMMENDED,
    RECOMMENDED_BREAK_MINUTES,
)

router = APIRouter()


def _require_planner(user: UserModel):
    if user.role not in ("admin", "gestionnaire"):
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs et gestionnaires")


def _can_manage_user(actor: UserModel, target: UserModel) -> bool:
    actor_city = (actor.ville or "").strip().lower() if getattr(actor, "ville", None) else None
    target_city = (target.ville or "").strip().lower() if getattr(target, "ville", None) else None
    if actor.role == "admin":
        return target.role in ("agent", "chauffeur", "gestionnaire")
    if actor.role == "gestionnaire":
        if target.role not in ("agent", "chauffeur"):
            return False
        # Gestionnaire limité aux profils de sa ville
        return bool(actor_city and target_city and actor_city == target_city)
    return False


def _parse_hhmm(s: str) -> time:
    parts = s.strip().split(":")
    if len(parts) != 2:
        raise ValueError
    return time(int(parts[0]), int(parts[1]))


def _shift_duration_hours(start: time, end: time) -> float:
    t0 = timedelta(hours=start.hour, minutes=start.minute)
    t1 = timedelta(hours=end.hour, minutes=end.minute)
    if t1 <= t0:
        t1 += timedelta(days=1)
    return (t1 - t0).total_seconds() / 3600.0


def _shift_interval(work_date: datetime, start: time, end: time) -> tuple[datetime, datetime]:
    """Construit l'intervalle [début, fin) du quart pour la date donnée."""
    start_dt = datetime.combine(work_date.date(), start)
    end_dt = datetime.combine(work_date.date(), end)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt


def _intervals_overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def _assert_no_staff_shift_overlap(
    db: Session,
    user_id: int,
    work_date: datetime,
    start: time,
    end: time,
    exclude_shift_id: int | None = None,
) -> None:
    """Empêche qu'un même utilisateur ait deux quarts qui se chevauchent."""
    new_start, new_end = _shift_interval(work_date, start, end)

    day_before = work_date - timedelta(days=1)
    day_after = work_date + timedelta(days=1)
    q = db.query(StaffShiftModel).filter(
        StaffShiftModel.user_id == user_id,
        StaffShiftModel.work_date >= day_before,
        StaffShiftModel.work_date <= day_after,
    )
    if exclude_shift_id is not None:
        q = q.filter(StaffShiftModel.id != exclude_shift_id)

    for existing in q.all():
        ex_start, ex_end = _shift_interval(existing.work_date, existing.start_time, existing.end_time)
        if _intervals_overlap(new_start, new_end, ex_start, ex_end):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Conflit d'horaire : ce membre du personnel a déjà un quart qui chevauche "
                    f"({existing.start_time.strftime('%H:%M')}-{existing.end_time.strftime('%H:%M')}) "
                    f"le {existing.work_date.date().isoformat()}."
                ),
            )


@router.get("/schedulable-overview")
def schedulable_overview(
    ville: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Vue pour l’interface Horaires équipe : listes séparées selon les droits."""
    _require_planner(current_user)

    admin_city = (ville or "").strip().lower() if ville else None
    actor_city = (current_user.ville or "").strip().lower() if getattr(current_user, "ville", None) else None

    chauffeurs_q = db.query(ChauffeurModel)
    agents_q = db.query(UserModel).filter(UserModel.role == "agent", UserModel.is_active.isnot(False))

    # En mode "ville active" côté admin, on limite la vue à cette ville.
    if current_user.role == "admin" and admin_city:
        chauffeurs_q = chauffeurs_q.filter(func.lower(ChauffeurModel.ville) == admin_city)
        agents_q = agents_q.filter(func.lower(UserModel.ville) == admin_city)
    # Un gestionnaire reste limité à sa ville.
    elif current_user.role == "gestionnaire" and actor_city:
        chauffeurs_q = chauffeurs_q.filter(func.lower(ChauffeurModel.ville) == actor_city)
        agents_q = agents_q.filter(func.lower(UserModel.ville) == actor_city)

    chauffeurs = chauffeurs_q.order_by(ChauffeurModel.nom).all()
    agents = agents_q.order_by(UserModel.username).all()

    gestionnaires = []
    if current_user.role == "admin":
        gestionnaires_q = db.query(UserModel).filter(
            UserModel.role == "gestionnaire",
            UserModel.is_active.isnot(False),
        )
        if admin_city:
            gestionnaires_q = gestionnaires_q.filter(func.lower(UserModel.ville) == admin_city)
        gestionnaires = gestionnaires_q.order_by(UserModel.username).all()

    return {
        "chauffeurs": [
            {"id": c.id, "nom": c.nom, "prenom": c.prenom, "statut": c.statut, "user_id": c.user_id}
            for c in chauffeurs
        ],
        "agents": [
            {"id": u.id, "username": u.username, "first_name": u.first_name, "last_name": u.last_name}
            for u in agents
        ],
        "gestionnaires": [
            {"id": u.id, "username": u.username, "first_name": u.first_name, "last_name": u.last_name}
            for u in gestionnaires
        ],
        "can_manage_gestionnaires": current_user.role == "admin",
    }


@router.get("/staff-shifts/{user_id}", response_model=List[StaffShiftOut])
def list_shifts_for_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _require_planner(current_user)
    target = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if not _can_manage_user(current_user, target):
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas gérer l'horaire de ce profil")

    shifts = (
        db.query(StaffShiftModel)
        .filter(StaffShiftModel.user_id == user_id)
        .order_by(StaffShiftModel.work_date.desc())
        .limit(200)
        .all()
    )
    out = []
    for s in shifts:
        out.append(
            StaffShiftOut(
                id=s.id,
                user_id=s.user_id,
                work_date=s.work_date,
                start_time=s.start_time.strftime("%H:%M"),
                end_time=s.end_time.strftime("%H:%M"),
                timezone=s.timezone or DEFAULT_TIMEZONE,
                break_minutes=s.break_minutes or 0,
                notes=s.notes,
            )
        )
    return out


def _validate_shift_times(start: time, end: time, break_minutes: int) -> None:
    dur = _shift_duration_hours(start, end)
    if dur <= 0:
        raise HTTPException(status_code=400, detail="Horaire invalide (fin après début)")
    if dur > MAX_SHIFT_HOURS:
        raise HTTPException(
            status_code=400,
            detail=f"Durée du quart trop longue (max {MAX_SHIFT_HOURS} h — vérifier la saisie)",
        )
    if dur >= HOURS_BEFORE_BREAK_RECOMMENDED and break_minutes < RECOMMENDED_BREAK_MINUTES:
        # Avertissement soft : on autorise mais on recommande
        pass


@router.post("/staff-shifts", response_model=StaffShiftOut)
def create_staff_shift(
    body: StaffShiftCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _require_planner(current_user)
    target = db.query(UserModel).filter(UserModel.id == body.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if not _can_manage_user(current_user, target):
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas gérer l'horaire de ce profil")

    try:
        st = _parse_hhmm(body.start_time)
        en = _parse_hhmm(body.end_time)
    except Exception:
        raise HTTPException(status_code=400, detail="Heures invalides (format HH:MM)")

    _validate_shift_times(st, en, body.break_minutes)

    wd = body.work_date
    if isinstance(wd, datetime):
        wd_norm = wd.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        wd_norm = datetime.combine(wd, time(0, 0))

    row = StaffShiftModel(
        user_id=body.user_id,
        work_date=wd_norm,
        start_time=st,
        end_time=en,
        timezone=body.timezone or DEFAULT_TIMEZONE,
        break_minutes=body.break_minutes,
        notes=body.notes,
    )
    _assert_no_staff_shift_overlap(db, body.user_id, wd_norm, st, en)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_audit(
        db,
        action="create_staff_shift",
        resource_type="StaffShift",
        user_id=getattr(current_user, "id", None),
        resource_id=row.id,
        details={"target_user_id": row.user_id, "ville_gestionnaire": getattr(current_user, "ville", None)},
    )
    return StaffShiftOut(
        id=row.id,
        user_id=row.user_id,
        work_date=row.work_date,
        start_time=row.start_time.strftime("%H:%M"),
        end_time=row.end_time.strftime("%H:%M"),
        timezone=row.timezone,
        break_minutes=row.break_minutes,
        notes=row.notes,
    )


@router.put("/staff-shifts/{shift_id}", response_model=StaffShiftOut)
def update_staff_shift(
    shift_id: int,
    body: StaffShiftUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _require_planner(current_user)
    row = db.query(StaffShiftModel).filter(StaffShiftModel.id == shift_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quart introuvable")
    target = db.query(UserModel).filter(UserModel.id == row.user_id).first()
    if not target or not _can_manage_user(current_user, target):
        raise HTTPException(status_code=403, detail="Action interdite")

    data = body.model_dump(exclude_unset=True)
    if "start_time" in data and data["start_time"]:
        row.start_time = _parse_hhmm(data["start_time"])
    if "end_time" in data and data["end_time"]:
        row.end_time = _parse_hhmm(data["end_time"])
    if "work_date" in data and data["work_date"] is not None:
        wd = data["work_date"]
        row.work_date = wd.replace(hour=0, minute=0, second=0, microsecond=0) if isinstance(wd, datetime) else wd
    if "timezone" in data:
        row.timezone = data["timezone"]
    if "break_minutes" in data:
        row.break_minutes = data["break_minutes"] or 0
    if "notes" in data:
        row.notes = data["notes"]

    _validate_shift_times(row.start_time, row.end_time, row.break_minutes or 0)
    _assert_no_staff_shift_overlap(
        db,
        row.user_id,
        row.work_date if isinstance(row.work_date, datetime) else datetime.combine(row.work_date, time(0, 0)),
        row.start_time,
        row.end_time,
        exclude_shift_id=row.id,
    )

    db.commit()
    db.refresh(row)
    log_audit(
        db,
        action="update_staff_shift",
        resource_type="StaffShift",
        user_id=getattr(current_user, "id", None),
        resource_id=row.id,
        details={"target_user_id": row.user_id, "ville_gestionnaire": getattr(current_user, "ville", None)},
    )
    return StaffShiftOut(
        id=row.id,
        user_id=row.user_id,
        work_date=row.work_date,
        start_time=row.start_time.strftime("%H:%M"),
        end_time=row.end_time.strftime("%H:%M"),
        timezone=row.timezone,
        break_minutes=row.break_minutes,
        notes=row.notes,
    )


@router.delete("/staff-shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _require_planner(current_user)
    row = db.query(StaffShiftModel).filter(StaffShiftModel.id == shift_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quart introuvable")
    target = db.query(UserModel).filter(UserModel.id == row.user_id).first()
    if not target or not _can_manage_user(current_user, target):
        raise HTTPException(status_code=403, detail="Action interdite")
    db.delete(row)
    db.commit()
    log_audit(
        db,
        action="delete_staff_shift",
        resource_type="StaffShift",
        user_id=getattr(current_user, "id", None),
        resource_id=shift_id,
        details={"target_user_id": row.user_id, "ville_gestionnaire": getattr(current_user, "ville", None)},
    )
    return None
