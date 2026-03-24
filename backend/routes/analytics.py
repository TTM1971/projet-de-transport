from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, Date
from typing import List, Optional
from datetime import datetime, timedelta, date
from database import get_db
from models.billet import Billet as BilletModel
from models.bus import Bus as BusModel
from models.ligne import Ligne as LigneModel
from models.destination import Destination as DestinationModel
from models.atelier import Atelier as AtelierModel
from models.depart import Depart as DepartModel
from middleware.dependencies import admin_only, get_current_user

router = APIRouter()

@router.get("/agent/dashboard")
def get_agent_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Dashboard spécifique pour l'agent avec :
    - CA du jour
    - Billets vendus aujourd'hui
    - Départs disponibles (du jour et futurs uniquement)
    """
    if current_user.role != 'agent':
        raise HTTPException(status_code=403, detail="Cette route est réservée aux agents")
    
    aujourdhui = date.today()
    
    # CA du jour pour cet agent
    billets_aujourdhui = db.query(BilletModel).filter(
        func.date(BilletModel.date_achat) == aujourdhui,
        BilletModel.agent_id == current_user.id,
        BilletModel.statut.in_(["valide", "utilise"])
    ).all()
    
    ca_aujourdhui = sum(float(b.montant or 0) for b in billets_aujourdhui)
    billets_vendus_aujourdhui = len(billets_aujourdhui)
    
    # Départs disponibles (du jour et futurs uniquement, pas les passés)
    departs = db.query(DepartModel).filter(
        func.date(DepartModel.date_depart) >= aujourdhui,
        DepartModel.places_disponibles > 0,
        DepartModel.statut.in_(["programme", "en_cours"])
    ).order_by(DepartModel.date_depart, DepartModel.heure_depart).all()
    
    return {
        "ca_aujourdhui": ca_aujourdhui,
        "billets_vendus_aujourdhui": billets_vendus_aujourdhui,
        "departs_disponibles": len(departs),
        "departs": [
            {
                "id": d.id,
                "date_depart": d.date_depart.isoformat() if d.date_depart else None,
                "heure_depart": d.heure_depart.strftime("%H:%M") if d.heure_depart else None,
                "places_disponibles": d.places_disponibles,
                "prix": float(d.prix) if d.prix else None,
                "statut": d.statut
            }
            for d in departs
        ]
    }

@router.get("/dashboard/historical")
def get_historical_data(
    days: int = 30,
    ligne_id: Optional[int] = None,
    destination_id: Optional[int] = None,
    bus_id: Optional[int] = None,
    chauffeur_id: Optional[int] = None,
    ville: Optional[str] = None,
    start_date_param: Optional[str] = None,  # Format: YYYY-MM-DD
    end_date_param: Optional[str] = None,  # Format: YYYY-MM-DD
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    """
    Récupère les données historiques pour les graphiques du dashboard admin.
    Retourne les données agrégées par jour sur la période spécifiée.
    Supports des filtres: ligne, destination, bus, chauffeur, date range.
    """
    # Gérer les dates
    if start_date_param and end_date_param:
        try:
            start_date = datetime.strptime(start_date_param, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_param, "%Y-%m-%d")
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="La date de début doit être avant la date de fin")
        except ValueError:
            raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD")
    elif start_date_param or end_date_param:
        raise HTTPException(status_code=400, detail="Les deux paramètres start_date et end_date sont requis ensemble")
    else:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Le nombre de jours doit être entre 1 et 365")
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
    
    # Initialiser les données par jour
    daily_data = {}
    current = start_date.date()
    while current <= end_date.date():
        daily_data[current.isoformat()] = {
            "date": current.isoformat(),
            "chiffre_affaires": 0.0,
            "billets_vendus": 0,
            "bus_en_service": 0,
            "interventions_maintenance": 0,
            "lignes_actives": 0,
            "destinations": 0
        }
        current += timedelta(days=1)
    
    # Construire les filtres pour les billets
    billet_filters = [
        BilletModel.date_achat >= start_date,
        BilletModel.date_achat <= end_date
    ]
    
    if ligne_id:
        billet_filters.append(BilletModel.ligne_id == ligne_id)
    if destination_id:
        billet_filters.append(BilletModel.destination_id == destination_id)
    if bus_id:
        billet_filters.append(BilletModel.bus_id == bus_id)
    if chauffeur_id:
        billet_filters.append(BilletModel.chauffeur_id == chauffeur_id)
    if ville:
        city_prefix = f"{ville.strip().lower()},%"
        lignes_ids_city = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(city_prefix)).subquery()
        billet_filters.append(BilletModel.ligne_id.in_(lignes_ids_city))
    
    # Récupérer le chiffre d'affaires et billets vendus par jour
    billets_query = db.query(
        cast(BilletModel.date_achat, Date).label('date'),
        func.sum(BilletModel.montant).label('ca_total'),
        func.count(BilletModel.id).label('nb_billets')
    ).filter(and_(*billet_filters)).group_by(cast(BilletModel.date_achat, Date))
    
    billets = billets_query.all()
    
    for billet in billets:
        date_str = billet.date.isoformat() if isinstance(billet.date, datetime) else str(billet.date)
        if date_str in daily_data:
            daily_data[date_str]["chiffre_affaires"] = float(billet.ca_total or 0)
            daily_data[date_str]["billets_vendus"] = int(billet.nb_billets or 0)
    
    # Récupérer les bus en service (statut à un moment donné - on prend le dernier statut connu)
    bus_filters = [BusModel.statut == 'en_service']
    if bus_id:
        bus_filters.append(BusModel.id == bus_id)
    
    buses = db.query(BusModel).filter(and_(*bus_filters)).all()
    # Pour simplifier, on compte les bus en service (on pourrait améliorer avec historique)
    for bus in buses:
        # Pour chaque jour, si le bus est en service, on l'ajoute
        # Pour l'instant, on considère qu'un bus en_service reste en service toute la période
        for date_str in daily_data:
            daily_data[date_str]["bus_en_service"] += 1
    
    # Récupérer les interventions de maintenance par jour
    atelier_filters = [
        AtelierModel.date_entree >= start_date,
        AtelierModel.date_entree <= end_date
    ]
    
    interventions = db.query(
        cast(AtelierModel.date_entree, Date).label('date'),
        func.count(AtelierModel.id).label('nb_interventions')
    ).filter(and_(*atelier_filters)).group_by(cast(AtelierModel.date_entree, Date)).all()
    
    for intervention in interventions:
        date_str = intervention.date.isoformat() if isinstance(intervention.date, datetime) else str(intervention.date)
        if date_str in daily_data:
            daily_data[date_str]["interventions_maintenance"] = int(intervention.nb_interventions or 0)
    
    # Récupérer les lignes actives (on considère qu'une ligne avec des départs est active)
    departs_q = db.query(DepartModel.ligne_id).filter(
        DepartModel.date_depart >= start_date,
        DepartModel.date_depart <= end_date
    )
    if ville:
        city_prefix = f"{ville.strip().lower()},%"
        lignes_ids_city = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(city_prefix)).subquery()
        departs_q = departs_q.filter(DepartModel.ligne_id.in_(lignes_ids_city))
    ligne_ids_with_departs = departs_q.distinct().all()
    
    ligne_ids = [l[0] for l in ligne_ids_with_departs]
    
    # Pour chaque jour, compter les lignes uniques avec départs
    for date_str in daily_data:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        lines_day_q = db.query(DepartModel.ligne_id).filter(
            func.date(DepartModel.date_depart) == target_date
        )
        if ville:
            city_prefix = f"{ville.strip().lower()},%"
            lignes_ids_city = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(city_prefix)).subquery()
            lines_day_q = lines_day_q.filter(DepartModel.ligne_id.in_(lignes_ids_city))
        lignes_ce_jour = lines_day_q.distinct().count()
        daily_data[date_str]["lignes_actives"] = lignes_ce_jour
    
    # Récupérer les destinations actives
    destination_ids_with_billets = db.query(BilletModel.destination_id).filter(
        and_(*billet_filters)
    ).distinct().all()
    
    destination_ids = [d[0] for d in destination_ids_with_billets if d[0]]
    
    for date_str in daily_data:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        dest_day_q = db.query(BilletModel.destination_id).filter(
            func.date(BilletModel.date_achat) == target_date
        )
        if ville:
            city_prefix = f"{ville.strip().lower()},%"
            lignes_ids_city = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(city_prefix)).subquery()
            dest_day_q = dest_day_q.filter(BilletModel.ligne_id.in_(lignes_ids_city))
        destinations_ce_jour = dest_day_q.distinct().count()
        daily_data[date_str]["destinations"] = destinations_ce_jour
    
    return {
        "data": list(daily_data.values()),
        "filters": {
            "days": days if not start_date_param else None,
            "start_date": start_date_param,
            "end_date": end_date_param,
            "ligne_id": ligne_id,
            "destination_id": destination_id,
            "bus_id": bus_id,
            "chauffeur_id": chauffeur_id
            ,
            "ville": ville
        }
    }

@router.get("/dashboard/summary")
def get_dashboard_summary(
    ville: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    """
    Retourne un résumé des statistiques pour le dashboard admin
    """
    aujourdhui = date.today()
    
    # Chiffre d'affaires total et aujourd'hui
    ca_total_q = db.query(func.sum(BilletModel.montant)).filter(
        BilletModel.statut.in_(["valide", "utilise"])
    )
    if ville:
        city_prefix = f"{ville.strip().lower()},%"
        lignes_ids_city = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(city_prefix)).subquery()
        ca_total_q = ca_total_q.filter(BilletModel.ligne_id.in_(lignes_ids_city))
    ca_total = ca_total_q.scalar() or 0.0
    
    ca_aujourdhui_q = db.query(func.sum(BilletModel.montant)).filter(
        func.date(BilletModel.date_achat) == aujourdhui,
        BilletModel.statut.in_(["valide", "utilise"])
    )
    if ville:
        city_prefix = f"{ville.strip().lower()},%"
        lignes_ids_city = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(city_prefix)).subquery()
        ca_aujourdhui_q = ca_aujourdhui_q.filter(BilletModel.ligne_id.in_(lignes_ids_city))
    ca_aujourdhui = ca_aujourdhui_q.scalar() or 0.0
    
    # Billets
    total_billets_q = db.query(func.count(BilletModel.id)).filter(
        BilletModel.statut.in_(["valide", "utilise"])
    )
    if ville:
        city_prefix = f"{ville.strip().lower()},%"
        lignes_ids_city = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(city_prefix)).subquery()
        total_billets_q = total_billets_q.filter(BilletModel.ligne_id.in_(lignes_ids_city))
    total_billets = total_billets_q.scalar() or 0
    
    billets_aujourdhui_q = db.query(func.count(BilletModel.id)).filter(
        func.date(BilletModel.date_achat) == aujourdhui,
        BilletModel.statut.in_(["valide", "utilise"])
    )
    if ville:
        city_prefix = f"{ville.strip().lower()},%"
        lignes_ids_city = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(city_prefix)).subquery()
        billets_aujourdhui_q = billets_aujourdhui_q.filter(BilletModel.ligne_id.in_(lignes_ids_city))
    billets_aujourdhui = billets_aujourdhui_q.scalar() or 0
    
    # Bus
    buses_en_service = db.query(func.count(BusModel.id)).filter(
        BusModel.statut == 'en_service'
    ).scalar() or 0
    
    buses_maintenance = db.query(func.count(BusModel.id)).filter(
        BusModel.statut == 'en_maintenance'
    ).scalar() or 0
    
    # Lignes actives (avec des départs aujourd'hui ou futurs)
    lignes_actives_q = db.query(DepartModel.ligne_id).filter(
        func.date(DepartModel.date_depart) >= aujourdhui
    )
    if ville:
        city_prefix = f"{ville.strip().lower()},%"
        lignes_ids_city = db.query(LigneModel.id).filter(func.lower(LigneModel.point_depart).like(city_prefix)).subquery()
        lignes_actives_q = lignes_actives_q.filter(DepartModel.ligne_id.in_(lignes_ids_city))
    lignes_actives = lignes_actives_q.distinct().count()
    
    # Destinations
    if ville:
        destinations = db.query(func.count(DestinationModel.id)).filter(func.lower(DestinationModel.ville) == ville.strip().lower()).scalar() or 0
    else:
        destinations = db.query(func.count(DestinationModel.id)).scalar() or 0
    
    # Interventions en cours
    interventions_en_cours = db.query(func.count(AtelierModel.id)).filter(
        AtelierModel.statut == 'en_cours'
    ).scalar() or 0
    
    return {
        "chiffre_affaires_total": float(ca_total),
        "chiffre_affaires_aujourdhui": float(ca_aujourdhui),
        "total_billets": total_billets,
        "billets_aujourdhui": billets_aujourdhui,
        "buses_en_service": buses_en_service,
        "buses_maintenance": buses_maintenance,
        "lignes_actives": lignes_actives,
        "destinations": destinations,
        "interventions_en_cours": interventions_en_cours
    }
