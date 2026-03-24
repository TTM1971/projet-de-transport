from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from database import get_db
from models.depart import Depart as DepartModel
from models.destination import Destination as DestinationModel
from models.ligne import Ligne as LigneModel
from models.bus_chauffeur import BusChauffeur as BusChauffeurModel
from schemas.depart import DepartCreate, DepartUpdate, Depart as DepartSchema
from datetime import datetime, date, time, timedelta
from middleware.dependencies import get_current_user, gestionnaire_or_admin_only
from utils.driver_schedule import assert_no_driver_conflict, window_for_depart_fields
from services.driver_schedule_ml import predict_block_minutes

router = APIRouter()
MANDATORY_BREAK_MINUTES = 180


def _normalize_city(v: str | None) -> str | None:
    if v is None:
        return None
    s = v.strip()
    return s.lower() if s else None


def _compute_effective_block_minutes_for_ligne(
    db: Session,
    ligne_id: int,
    weekday: int,
    hour_float: float,
) -> int:
    ml_block = int(predict_block_minutes(weekday, hour_float, ligne_id))
    ligne = db.query(LigneModel).filter(LigneModel.id == ligne_id).first()
    ligne_minutes = int(ligne.duree_minutes) if ligne and ligne.duree_minutes else 0
    trip_minutes = max(ml_block, ligne_minutes)
    return trip_minutes + MANDATORY_BREAK_MINUTES

def get_bus_drivers(db: Session, bus_id: int):
    """
    Récupère les chauffeurs assignés à un bus (un jour, un nuit)
    Retourne un dict avec 'jour' et 'nuit' ou None si non assigné
    """
    assignations = db.query(BusChauffeurModel).filter(
        BusChauffeurModel.bus_id == bus_id,
        BusChauffeurModel.is_actif == True
    ).all()
    
    drivers = {'jour': None, 'nuit': None}
    for assignation in assignations:
        if assignation.type_affectation in ['jour', 'nuit']:
            drivers[assignation.type_affectation] = assignation.chauffeur_id
    
    return drivers

@router.get("/", response_model=List[DepartSchema])
def list_departs(
    skip: int = 0,
    limit: int = 100,
    ville: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Liste des départs - accessible à tous les utilisateurs authentifiés (agents peuvent consulter pour aider les clients)"""
    q = db.query(DepartModel)
    role = getattr(current_user, "role", None)
    city = None
    if role in ("agent", "gestionnaire"):
        city = _normalize_city(getattr(current_user, "ville", None))
    elif role == "admin" and ville:
        city = _normalize_city(ville)
    if city:
        city_ligne_ids = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(f"{city},%")).subquery()
        q = q.filter(DepartModel.ligne_id.in_(city_ligne_ids))
    elif role in ("agent", "gestionnaire"):
        q = q.filter(DepartModel.id == -1)
    departs = q.order_by(DepartModel.date_depart).offset(skip).limit(limit).all()
    return departs

@router.get("/date/{date_str}", response_model=List[DepartSchema])
def list_departs_by_date(
    date_str: str,
    ville: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Liste les départs pour une date spécifique (format: YYYY-MM-DD) - accessible aux agents pour consulter les horaires"""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_datetime = datetime.combine(target_date, time.min)
        end_datetime = datetime.combine(target_date, time.max)
        
        q = db.query(DepartModel).filter(
            and_(
                DepartModel.date_depart >= start_datetime,
                DepartModel.date_depart <= end_datetime
            )
        )
        role = getattr(current_user, "role", None)
        city = None
        if role in ("agent", "gestionnaire"):
            city = _normalize_city(getattr(current_user, "ville", None))
        elif role == "admin" and ville:
            city = _normalize_city(ville)
        if city:
            city_ligne_ids = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(f"{city},%")).subquery()
            q = q.filter(DepartModel.ligne_id.in_(city_ligne_ids))
        elif role in ("agent", "gestionnaire"):
            q = q.filter(DepartModel.id == -1)
        departs = q.order_by(DepartModel.heure_depart).all()
        return departs
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD")

@router.get("/ligne/{ligne_id}", response_model=List[DepartSchema])
def list_departs_by_ligne(ligne_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    role = getattr(current_user, "role", None)
    if role in ("agent", "gestionnaire"):
        city = _normalize_city(getattr(current_user, "ville", None))
        ligne = db.query(LigneModel).filter(LigneModel.id == ligne_id).first()
        if not city or not ligne or not ligne.point_depart or _normalize_city(ligne.point_depart.split(",")[0]) != city:
            raise HTTPException(status_code=403, detail="Accès interdit pour cette ligne")
    departs = db.query(DepartModel).filter(DepartModel.ligne_id == ligne_id).order_by(DepartModel.date_depart).all()
    return departs

@router.get("/{depart_id}", response_model=DepartSchema)
def get_depart(depart_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    depart = db.query(DepartModel).filter(DepartModel.id == depart_id).first()
    if not depart:
        raise HTTPException(status_code=404, detail="Départ non trouvé")
    role = getattr(current_user, "role", None)
    if role in ("agent", "gestionnaire"):
        city = _normalize_city(getattr(current_user, "ville", None))
        ligne = db.query(LigneModel).filter(LigneModel.id == depart.ligne_id).first()
        if not city or not ligne or _normalize_city((ligne.point_depart or "").split(",")[0]) != city:
            raise HTTPException(status_code=403, detail="Accès interdit pour ce départ")
    return depart

@router.get("/{depart_id}/billets/count")
def count_billets_for_depart(depart_id: int, db: Session = Depends(get_db)):
    """Compte le nombre de billets vendus pour un départ"""
    from models.billet import Billet as BilletModel
    count = db.query(BilletModel).filter(BilletModel.depart_id == depart_id).count()
    return {"depart_id": depart_id, "billets_vendus": count}

@router.post("/", response_model=DepartSchema)
def create_depart(depart: DepartCreate, db: Session = Depends(get_db), current_user = Depends(gestionnaire_or_admin_only)):
    from models.bus import Bus as BusModel
    from models.ligne import Ligne as LigneModel
    from models.chauffeur import Chauffeur as ChauffeurModel
    
    # Vérifier que la ligne existe
    ligne = db.query(LigneModel).filter(LigneModel.id == depart.ligne_id).first()
    if not ligne:
        raise HTTPException(status_code=404, detail=f"Ligne avec ID {depart.ligne_id} non trouvée")
    
    # Vérifier que la destination existe et récupérer son tarif
    destination = db.query(DestinationModel).filter(DestinationModel.id == depart.destination_id).first()
    if not destination:
        raise HTTPException(status_code=404, detail=f"Destination avec ID {depart.destination_id} non trouvée")
    
    # Vérifier que le bus existe
    bus = db.query(BusModel).filter(BusModel.id == depart.bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail=f"Bus avec ID {depart.bus_id} non trouvé")
    
    # Si aucun chauffeur n'est spécifié, assigner automatiquement les chauffeurs du bus
    chauffeur_id = depart.chauffeur_id
    if not chauffeur_id:
        drivers = get_bus_drivers(db, depart.bus_id)
        # Déterminer le chauffeur selon l'heure de départ
        heure_parts = depart.heure_depart.split(":")
        heure_value = int(heure_parts[0]) if len(heure_parts) > 0 else 8
        
        # Si heure < 18h, utiliser chauffeur jour, sinon chauffeur nuit
        if heure_value < 18:
            chauffeur_id = drivers['jour']
            if not chauffeur_id:
                raise HTTPException(
                    status_code=400, 
                    detail="Aucun chauffeur de jour assigné à ce bus. Veuillez assigner un chauffeur de jour au bus ou spécifier un chauffeur manuellement."
                )
        else:
            chauffeur_id = drivers['nuit']
            if not chauffeur_id:
                raise HTTPException(
                    status_code=400, 
                    detail="Aucun chauffeur de nuit assigné à ce bus. Veuillez assigner un chauffeur de nuit au bus ou spécifier un chauffeur manuellement."
                )
    else:
        # Vérifier que le chauffeur existe
        chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == chauffeur_id).first()
        if not chauffeur:
            raise HTTPException(status_code=404, detail=f"Chauffeur avec ID {chauffeur_id} non trouvé")
    
    # Récupérer le prix depuis la destination
    prix = destination.tarif
    
    # Convertir heure_depart de string "HH:MM" en time
    try:
        heure_parts = depart.heure_depart.split(":")
        if len(heure_parts) != 2:
            raise ValueError
        heure_time = time(int(heure_parts[0]), int(heure_parts[1]))
        if not (0 <= int(heure_parts[0]) <= 23 and 0 <= int(heure_parts[1]) <= 59):
            raise ValueError
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Format d'heure invalide. Utilisez HH:MM (ex: 08:30)")
    
    # Vérifier le statut
    valid_status = ['programme', 'en_cours', 'termine', 'annule']
    if depart.statut and depart.statut not in valid_status:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Statuts acceptés: {', '.join(valid_status)}")
    
    # Vérifier les places disponibles
    if depart.places_disponibles < 0:
        raise HTTPException(status_code=400, detail="Le nombre de places disponibles ne peut pas être négatif")
    
    # Combiner date_depart et heure_depart
    date_depart = depart.date_depart
    if isinstance(date_depart, date) and not isinstance(date_depart, datetime):
        date_depart = datetime.combine(date_depart, heure_time)
    else:
        date_depart = datetime.combine(date_depart.date(), heure_time)
    
    # Vérifier que la date n'est pas dans le passé
    if date_depart < datetime.utcnow():
        raise HTTPException(status_code=400, detail="La date de départ ne peut pas être dans le passé")

    wd = date_depart.weekday()
    hr = float(heure_time.hour + heure_time.minute / 60.0)
    block = _compute_effective_block_minutes_for_ligne(db, depart.ligne_id, wd, hr)
    ws, we = window_for_depart_fields(date_depart, heure_time, block)
    assert_no_driver_conflict(db, chauffeur_id, ws, we, exclude_depart_id=None, block_minutes=block)

    db_depart = DepartModel(
        ligne_id=depart.ligne_id,
        destination_id=depart.destination_id,
        bus_id=depart.bus_id,
        chauffeur_id=chauffeur_id,
        date_depart=date_depart,
        heure_depart=heure_time,
        places_disponibles=depart.places_disponibles,
        prix=prix,
        statut=depart.statut
    )
    db.add(db_depart)
    db.commit()
    db.refresh(db_depart)
    return db_depart

@router.post("/generate-future", response_model=List[DepartSchema])
def generate_future_departs(
    start_date: str = Query(..., description="Date de début (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Date de fin (YYYY-MM-DD)"),
    ligne_id: int = Query(..., description="ID de la ligne"),
    destination_id: int = Query(..., description="ID de la destination"),
    bus_id: int = Query(..., description="ID du bus"),
    heure_depart: str = Query("08:00", description="Heure de départ (HH:MM)"),
    jours_semaine: Optional[str] = Query(None, description="Jours de la semaine (ex: '0,1,2,3,4,5,6' pour tous les jours, 0=lundi)"),
    db: Session = Depends(get_db),
    current_user = Depends(gestionnaire_or_admin_only)
):
    """
    Génère automatiquement des départs futurs pour une période donnée.
    Les chauffeurs sont assignés automatiquement selon l'heure (jour < 18h, nuit >= 18h).
    """
    from models.bus import Bus as BusModel
    from models.ligne import Ligne as LigneModel
    
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start < date.today():
            raise HTTPException(status_code=400, detail="La date de début doit être aujourd'hui ou une date future")
        if end < start:
            raise HTTPException(status_code=400, detail="La date de fin doit être après la date de début")
        
        # Vérifier que le bus existe
        bus = db.query(BusModel).filter(BusModel.id == bus_id).first()
        if not bus:
            raise HTTPException(status_code=404, detail=f"Bus avec ID {bus_id} non trouvé")
        
        # Vérifier que la ligne existe
        ligne = db.query(LigneModel).filter(LigneModel.id == ligne_id).first()
        if not ligne:
            raise HTTPException(status_code=404, detail=f"Ligne avec ID {ligne_id} non trouvée")
        
        # Vérifier que la destination existe
        destination = db.query(DestinationModel).filter(DestinationModel.id == destination_id).first()
        if not destination:
            raise HTTPException(status_code=404, detail=f"Destination avec ID {destination_id} non trouvée")
        
        # Récupérer les chauffeurs assignés au bus
        drivers = get_bus_drivers(db, bus_id)
        if not drivers['jour'] or not drivers['nuit']:
            raise HTTPException(
                status_code=400,
                detail=f"Le bus doit avoir deux chauffeurs assignés (un jour, un nuit) avant de générer des départs. Chauffeurs actuellement assignés: Jour={'Oui' if drivers['jour'] else 'Non'}, Nuit={'Oui' if drivers['nuit'] else 'Non'}"
            )
        
        # Parser l'heure
        heure_parts = heure_depart.split(":")
        if len(heure_parts) != 2:
            raise HTTPException(status_code=400, detail="Format d'heure invalide. Utilisez HH:MM")
        heure_value = int(heure_parts[0])
        heure_time = time(int(heure_parts[0]), int(heure_parts[1]))
        
        # Déterminer le chauffeur selon l'heure
        chauffeur_id = drivers['jour'] if heure_value < 18 else drivers['nuit']
        
        # Parser les jours de la semaine (optionnel)
        allowed_days = None
        if jours_semaine:
            try:
                allowed_days = [int(d.strip()) for d in jours_semaine.split(',')]
                if not all(0 <= d <= 6 for d in allowed_days):
                    raise ValueError
            except ValueError:
                raise HTTPException(status_code=400, detail="Format invalide pour jours_semaine. Utilisez '0,1,2,3,4,5,6' (0=lundi)")
        
        # Générer les départs
        created_departs = []
        current = start
        prix = destination.tarif
        DRIVER_ASSISTANT_SEATS = 2
        
        while current <= end:
            # Si jours_semaine est spécifié, vérifier que c'est un jour autorisé
            # weekday() retourne 0=lundi, 6=dimanche
            if allowed_days is None or current.weekday() in allowed_days:
                # Vérifier si un départ existe déjà pour cette date/heure/bus
                existing = db.query(DepartModel).filter(
                    DepartModel.bus_id == bus_id,
                    DepartModel.ligne_id == ligne_id,
                    func.date(DepartModel.date_depart) == current,
                    DepartModel.heure_depart == heure_time
                ).first()
                
                if not existing:
                    date_depart_dt = datetime.combine(current, heure_time)
                    places_disponibles = bus.capacite - DRIVER_ASSISTANT_SEATS
                    
                    db_depart = DepartModel(
                        ligne_id=ligne_id,
                        destination_id=destination_id,
                        bus_id=bus_id,
                        chauffeur_id=chauffeur_id,
                        date_depart=date_depart_dt,
                        heure_depart=heure_time,
                        places_disponibles=places_disponibles,
                        prix=prix,
                        statut='programme'
                    )
                    db.add(db_depart)
                    created_departs.append(db_depart)
            
            current += timedelta(days=1)
        
        db.commit()
        
        # Rafraîchir les objets pour obtenir les IDs
        for dep in created_departs:
            db.refresh(dep)
        
        return created_departs
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Format de date invalide: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")

@router.put("/{depart_id}", response_model=DepartSchema)
def update_depart(depart_id: int, depart_update: DepartUpdate, db: Session = Depends(get_db), current_user = Depends(gestionnaire_or_admin_only)):
    from models.ligne import Ligne as LigneModel
    from models.bus import Bus as BusModel
    from models.chauffeur import Chauffeur as ChauffeurModel

    db_depart = db.query(DepartModel).filter(DepartModel.id == depart_id).first()
    if not db_depart:
        raise HTTPException(status_code=404, detail="Départ non trouvé")
    
    update_data = depart_update.model_dump(exclude_unset=True)
    
    # Valider ligne_id si présent
    if "ligne_id" in update_data and update_data["ligne_id"] is not None:
        ligne = db.query(LigneModel).filter(LigneModel.id == update_data["ligne_id"]).first()
        if not ligne:
            raise HTTPException(status_code=404, detail=f"Ligne avec ID {update_data['ligne_id']} non trouvée")

    # Si destination_id est modifié, récupérer le nouveau prix
    if "destination_id" in update_data and update_data["destination_id"] is not None:
        destination = db.query(DestinationModel).filter(DestinationModel.id == update_data["destination_id"]).first()
        if not destination:
            raise HTTPException(status_code=404, detail=f"Destination avec ID {update_data['destination_id']} non trouvée")
        # Mettre à jour automatiquement le prix depuis la nouvelle destination
        update_data["prix"] = destination.tarif
    
    # Valider bus_id si présent
    if "bus_id" in update_data and update_data["bus_id"] is not None:
        bus = db.query(BusModel).filter(BusModel.id == update_data["bus_id"]).first()
        if not bus:
            raise HTTPException(status_code=404, detail=f"Bus avec ID {update_data['bus_id']} non trouvé")

    # Valider chauffeur_id si présent
    if "chauffeur_id" in update_data and update_data["chauffeur_id"] is not None:
        chauffeur = db.query(ChauffeurModel).filter(ChauffeurModel.id == update_data["chauffeur_id"]).first()
        if not chauffeur:
            raise HTTPException(status_code=404, detail=f"Chauffeur avec ID {update_data['chauffeur_id']} non trouvé")

    # Gérer la conversion de l'heure si présente
    if "heure_depart" in update_data and update_data["heure_depart"]:
        try:
            heure_parts = update_data["heure_depart"].split(":")
            if len(heure_parts) != 2:
                raise ValueError
            update_data["heure_depart"] = time(int(heure_parts[0]), int(heure_parts[1]))
            if not (0 <= int(heure_parts[0]) <= 23 and 0 <= int(heure_parts[1]) <= 59):
                raise ValueError
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Format d'heure invalide. Utilisez HH:MM (ex: 08:30)")
    
    # Valider le statut si présent
    if "statut" in update_data and update_data["statut"]:
        valid_status = ['programme', 'en_cours', 'termine', 'annule']
        if update_data["statut"] not in valid_status:
            raise HTTPException(status_code=400, detail=f"Statut invalide. Statuts acceptés: {', '.join(valid_status)}")

    # Valider places_disponibles si présent
    if "places_disponibles" in update_data and update_data["places_disponibles"] < 0:
        raise HTTPException(status_code=400, detail="Le nombre de places disponibles ne peut pas être négatif")

    # Gérer la combinaison date/heure si les deux sont présents
    if "date_depart" in update_data and "heure_depart" in update_data:
        date_depart = update_data["date_depart"]
        heure_depart = update_data["heure_depart"]
        if isinstance(date_depart, date) and not isinstance(date_depart, datetime):
            update_data["date_depart"] = datetime.combine(date_depart, heure_depart)
        elif isinstance(date_depart, datetime):
            update_data["date_depart"] = datetime.combine(date_depart.date(), heure_depart)
    elif "date_depart" in update_data and not ("heure_depart" in update_data):
        # Si seule la date est mise à jour, conserver l'heure existante
        date_depart = update_data["date_depart"]
        heure_depart = db_depart.heure_depart
        if isinstance(date_depart, date) and not isinstance(date_depart, datetime):
            update_data["date_depart"] = datetime.combine(date_depart, heure_depart)
        elif isinstance(date_depart, datetime):
            update_data["date_depart"] = datetime.combine(date_depart.date(), heure_depart)
    elif "heure_depart" in update_data and not ("date_depart" in update_data):
        # Si seule l'heure est mise à jour, conserver la date existante
        date_depart = db_depart.date_depart
        heure_depart = update_data["heure_depart"]
        update_data["date_depart"] = datetime.combine(date_depart.date(), heure_depart)

    # Vérifier que la date n'est pas dans le passé si elle est mise à jour
    if "date_depart" in update_data and update_data["date_depart"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="La date de départ ne peut pas être dans le passé")

    for field, value in update_data.items():
        setattr(db_depart, field, value)

    # Conflits chauffeur après mise à jour
    final_ch = db_depart.chauffeur_id
    final_date = db_depart.date_depart
    final_heure = db_depart.heure_depart
    if final_ch and final_date and final_heure:
        wd = final_date.weekday()
        hr = float(final_heure.hour + final_heure.minute / 60.0)
        block = _compute_effective_block_minutes_for_ligne(db, db_depart.ligne_id, wd, hr)
        ws, we = window_for_depart_fields(final_date, final_heure, block)
        assert_no_driver_conflict(db, final_ch, ws, we, exclude_depart_id=depart_id, block_minutes=block)

    db.commit()
    db.refresh(db_depart)
    return db_depart

@router.delete("/{depart_id}")
def delete_depart(depart_id: int, db: Session = Depends(get_db), current_user = Depends(gestionnaire_or_admin_only)):
    db_depart = db.query(DepartModel).filter(DepartModel.id == depart_id).first()
    if not db_depart:
        raise HTTPException(status_code=404, detail="Départ non trouvé")
    
    db.delete(db_depart)
    db.commit()
    return {"message": "Départ supprimé avec succès"}
