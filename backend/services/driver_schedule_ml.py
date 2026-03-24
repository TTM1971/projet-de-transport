"""
Apprentissage automatique (scikit-learn) pour estimer une durée de blocage / score de faisabilité
à partir de l'historique des départs (même chauffeur, espacements observés).

- Entraîne un RandomForestRegressor sur : (jour_semaine, heure, ligne_id) -> écart moyen observé (minutes)
- Sauvegarde le modèle dans backend/ml_models/driver_schedule_rf.joblib
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
from sqlalchemy.orm import Session

from models.depart import Depart as DepartModel

try:
    import joblib
    from sklearn.ensemble import RandomForestRegressor
except ImportError:  # pragma: no cover
    joblib = None
    RandomForestRegressor = None

MODEL_DIR = Path(__file__).resolve().parent.parent / "ml_models"
MODEL_PATH = MODEL_DIR / "driver_schedule_rf.joblib"

MIN_SAMPLES = 8


def _ensure_dir() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


def train_model_from_db(db: Session) -> dict[str, Any]:
    """Construit un jeu de données à partir des départs terminés / programmés et entraîne le modèle."""
    if joblib is None or RandomForestRegressor is None:
        return {"ok": False, "message": "scikit-learn / joblib non installés (pip install scikit-learn joblib)"}

    departs = (
        db.query(DepartModel)
        .filter(DepartModel.statut.in_(["termine", "programme", "en_cours"]))
        .order_by(DepartModel.chauffeur_id, DepartModel.date_depart)
        .all()
    )

    X: list[list[float]] = []
    y: list[float] = []

    by_driver: dict[int, list[DepartModel]] = {}
    for d in departs:
        by_driver.setdefault(d.chauffeur_id, []).append(d)

    for cid, lst in by_driver.items():
        lst.sort(key=lambda x: x.date_depart)
        for prev, cur in zip(lst, lst[1:]):
            try:
                t0 = datetime.combine(prev.date_depart.date(), prev.heure_depart)
                t1 = datetime.combine(cur.date_depart.date(), cur.heure_depart)
            except Exception:
                continue
            gap_min = max(0.0, (t1 - t0).total_seconds() / 60.0)
            if gap_min < 5 or gap_min > 24 * 60:
                continue
            wd = float(cur.date_depart.weekday())
            hr = float(cur.heure_depart.hour + cur.heure_depart.minute / 60.0)
            lid = float(cur.ligne_id)
            X.append([wd, hr, lid])
            y.append(gap_min)

    if len(y) < MIN_SAMPLES:
        # Données synthétiques minimales pour permettre un premier entraînement
        rng = np.random.default_rng(42)
        for _ in range(40):
            X.append(
                [
                    float(rng.integers(0, 7)),
                    float(rng.integers(6, 22)),
                    float(rng.integers(1, 20)),
                ]
            )
            y.append(float(rng.uniform(45.0, 180.0)))

    X_arr = np.array(X, dtype=np.float64)
    y_arr = np.array(y, dtype=np.float64)

    model = RandomForestRegressor(
        n_estimators=80,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_arr, y_arr)

    _ensure_dir()
    joblib.dump(model, MODEL_PATH)

    return {
        "ok": True,
        "samples": len(y),
        "model_path": str(MODEL_PATH),
        "message": "Modèle entraîné et sauvegardé.",
    }


def load_model():
    if joblib is None or not MODEL_PATH.is_file():
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def predict_block_minutes(
    weekday: int,
    hour_float: float,
    ligne_id: int,
    fallback: float = 90.0,
) -> float:
    """Prédit une durée de blocage (minutes) entre deux services, utilisée pour le scoring / suggestions."""
    model = load_model()
    if model is None:
        return fallback
    try:
        x = np.array([[float(weekday), float(hour_float), float(ligne_id)]], dtype=np.float64)
        pred = float(model.predict(x)[0])
        return max(30.0, min(240.0, pred))
    except Exception:
        return fallback


def score_slot_feasibility(
    weekday: int,
    hour_float: float,
    ligne_id: int,
) -> float:
    """Score plus élevé = créneau plus favorable (simple normalisation inverse de la charge prédite)."""
    block = predict_block_minutes(weekday, hour_float, ligne_id)
    # moins de blocage prédit => score plus haut (arbitraire mais stable)
    return max(0.0, 200.0 - block)
