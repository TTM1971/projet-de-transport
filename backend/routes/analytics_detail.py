"""
Routes pour les détails granulaires des analytics
Permet de descendre jusqu'au niveau transaction/trajet
Optimisé pour éviter les problèmes N+1 et les timeouts
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from database import get_db
from models.billet import Billet as BilletModel
from models.depart import Depart as DepartModel
from models.bus import Bus as BusModel
from models.chauffeur import Chauffeur as ChauffeurModel
from models.user import User as UserModel
from models.ligne import Ligne as LigneModel
from models.destination import Destination as DestinationModel
from models.bus_chauffeur import BusChauffeur as BusChauffeurModel
from middleware.dependencies import admin_only

router = APIRouter()

def _calculate_arrival_time(heure_depart, duree_minutes):
    """Calcule l'heure d'arrivée estimée basée sur l'heure de départ et la durée"""
    if not heure_depart or not duree_minutes:
        return None
    try:
        from datetime import time as dt_time
        
        # Si c'est un objet time, utiliser directement
        if hasattr(heure_depart, 'hour'):
            minutes_depart = heure_depart.hour * 60 + heure_depart.minute
        # Si c'est une chaîne "HH:MM"
        elif isinstance(heure_depart, str):
            parts = heure_depart.split(':')
            if len(parts) >= 2:
                minutes_depart = int(parts[0]) * 60 + int(parts[1])
            else:
                return None
        else:
            return None
        
        minutes_arrivee = minutes_depart + duree_minutes
        
        # Convertir en heures:minutes
        heures_arrivee = (minutes_arrivee // 60) % 24
        min_arrivee = minutes_arrivee % 60
        
        return f"{heures_arrivee:02d}:{min_arrivee:02d}"
    except Exception as e:
        print(f"Erreur calcul heure arrivée: {e}")
        return None

@router.get("/chiffre-affaires/jours")
def get_chiffre_affaires_par_jour(
    start_date: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    """
    Retourne le chiffre d'affaires par jour avec tous les détails
    Optimisé pour éviter les requêtes N+1
    """
    try:
        # Parser les dates
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start = date.today() - timedelta(days=30)
        
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end = date.today()
        
        # Limiter la période à 90 jours maximum pour éviter les requêtes trop lourdes
        if (end - start).days > 90:
            raise HTTPException(
                status_code=400, 
                detail="La période ne peut pas dépasser 90 jours. Veuillez réduire la plage de dates."
            )
        
        # OPTIMISATION: Récupérer tous les billets avec leurs relations en une seule requête
        # Limite à 15000 billets pour éviter les timeouts et les réponses trop lourdes
        billets_query = db.query(BilletModel).filter(
            func.date(BilletModel.date_achat) >= start,
            func.date(BilletModel.date_achat) <= end,
            BilletModel.statut.in_(["valide", "utilise"])
        ).order_by(BilletModel.date_achat)
        
        # Compter d'abord le total
        total_billets = billets_query.count()
        billets = billets_query.limit(15000).all()
        limite_atteinte = total_billets > len(billets)
        
        # OPTIMISATION: Précharger toutes les données nécessaires en mémoire
        # Récupérer tous les IDs uniques
        depart_ids = list(set([b.depart_id for b in billets if b.depart_id]))
        agent_ids = list(set([b.agent_id for b in billets if b.agent_id]))
        bus_ids = list(set([b.bus_id for b in billets if b.bus_id]))
        destination_ids = list(set([b.destination_id for b in billets if b.destination_id]))
        
        # Charger tous les départs en une seule requête
        departs_dict = {}
        if depart_ids:
            departs = db.query(DepartModel).filter(DepartModel.id.in_(depart_ids)).all()
            departs_dict = {d.id: d for d in departs}
            
            # Récupérer les IDs supplémentaires pour les relations
            ligne_ids = list(set([d.ligne_id for d in departs if d.ligne_id]))
            bus_ids.extend([d.bus_id for d in departs if d.bus_id])
            destination_ids.extend([d.destination_id for d in departs if d.destination_id])
            chauffeur_ids = list(set([d.chauffeur_id for d in departs if d.chauffeur_id]))
            
            # Charger toutes les relations des départs
            buses_dict = {b.id: b for b in db.query(BusModel).filter(BusModel.id.in_(bus_ids)).all()}
            lignes_dict = {l.id: l for l in db.query(LigneModel).filter(LigneModel.id.in_(ligne_ids)).all()}
            destinations_dict = {d.id: d for d in db.query(DestinationModel).filter(DestinationModel.id.in_(destination_ids)).all()}
            chauffeurs_dict = {c.id: c for c in db.query(ChauffeurModel).filter(ChauffeurModel.id.in_(chauffeur_ids)).all()}
            
            # Charger toutes les assignations de bus
            bus_chauffeurs_dict = {}
            if bus_ids:
                assignations = db.query(BusChauffeurModel).filter(
                    BusChauffeurModel.bus_id.in_(bus_ids),
                    BusChauffeurModel.is_actif == True
                ).all()
                for assign in assignations:
                    if assign.bus_id not in bus_chauffeurs_dict:
                        bus_chauffeurs_dict[assign.bus_id] = []
                    bus_chauffeurs_dict[assign.bus_id].append(assign)
        else:
            buses_dict = {}
            lignes_dict = {}
            destinations_dict = {}
            chauffeurs_dict = {}
            bus_chauffeurs_dict = {}
        
        # Charger tous les agents en une seule requête
        agents_dict = {}
        if agent_ids:
            agents = db.query(UserModel).filter(UserModel.id.in_(agent_ids)).all()
            agents_dict = {a.id: a for a in agents}
        
        # Grouper par jour
        ca_par_jour = {}
        
        for billet in billets:
            jour = billet.date_achat.date() if isinstance(billet.date_achat, datetime) else billet.date_achat
            jour_str = jour.isoformat() if isinstance(jour, date) else str(jour)
            
            if jour_str not in ca_par_jour:
                ca_par_jour[jour_str] = {
                    "date": jour_str,
                    "chiffre_affaires_total": 0,
                    "nombre_transactions": 0,
                    "trajets": {},
                    "caissieres": {},
                    "buses": {},
                    "destinations": {}
                }
            
            ca_par_jour[jour_str]["chiffre_affaires_total"] += float(billet.montant or 0)
            ca_par_jour[jour_str]["nombre_transactions"] += 1
            
            # Trajets (départs)
            if billet.depart_id and billet.depart_id in departs_dict:
                depart_id = billet.depart_id
                depart = departs_dict[depart_id]
                
                if depart_id not in ca_par_jour[jour_str]["trajets"]:
                    bus = buses_dict.get(depart.bus_id)
                    ligne = lignes_dict.get(depart.ligne_id)
                    destination = destinations_dict.get(depart.destination_id)
                    chauffeur = chauffeurs_dict.get(depart.chauffeur_id)
                    
                    # Récupérer les chauffeurs assignés depuis le cache
                    assignations = bus_chauffeurs_dict.get(depart.bus_id, [])
                    
                    ca_par_jour[jour_str]["trajets"][depart_id] = {
                        "depart_id": depart_id,
                        "bus": {
                            "id": bus.id if bus else None,
                            "immatriculation": bus.immatriculation if bus else None,
                            "marque": bus.marque if bus else None,
                            "modele": bus.modele if bus else None
                        } if bus else None,
                        "ligne": {
                            "id": ligne.id if ligne else None,
                            "numero": ligne.numero if ligne else None,
                            "point_depart": ligne.point_depart if ligne else None,
                            "point_arrivee": ligne.point_arrivee if ligne else None
                        } if ligne else None,
                        "destination": {
                            "id": destination.id if destination else None,
                            "nom": destination.nom if destination else None,
                            "ville": destination.ville if destination else None
                        } if destination else None,
                        "chauffeur": {
                            "id": chauffeur.id if chauffeur else None,
                            "nom": chauffeur.nom if chauffeur else None,
                            "prenom": chauffeur.prenom if chauffeur else None,
                            "numero_permis": chauffeur.numero_permis if chauffeur else None
                        } if chauffeur else None,
                        "chauffeurs_assignes": [
                            {
                                "id": assign.chauffeur_id,
                                "type": assign.type_affectation,
                                "nom": chauffeurs_dict.get(assign.chauffeur_id).nom if chauffeurs_dict.get(assign.chauffeur_id) else None,
                                "prenom": chauffeurs_dict.get(assign.chauffeur_id).prenom if chauffeurs_dict.get(assign.chauffeur_id) else None
                            }
                            for assign in assignations
                            if chauffeurs_dict.get(assign.chauffeur_id)
                        ],
                        "heure_depart": depart.heure_depart.strftime("%H:%M") if depart.heure_depart else None,
                        "date_depart": depart.date_depart.isoformat() if depart.date_depart else None,
                        "billets": [],
                        "ca_du_trajet": 0,
                        "nombre_billets": 0
                    }
                
                # Ajouter le billet au trajet (limiter à 500 billets par trajet pour éviter les réponses trop lourdes)
                if len(ca_par_jour[jour_str]["trajets"][depart_id]["billets"]) < 500:
                    agent = agents_dict.get(billet.agent_id)
                    ca_par_jour[jour_str]["trajets"][depart_id]["billets"].append({
                        "id": billet.id,
                        "montant": float(billet.montant or 0),
                        "caissiere": {
                            "id": agent.id if agent else None,
                            "username": agent.username if agent else None,
                            "first_name": agent.first_name if agent else None,
                            "last_name": agent.last_name if agent else None
                        } if agent else None,
                        "nom_client": billet.nom_client,
                        "telephone_client": billet.telephone_client,
                        "mode_paiement": billet.mode_paiement,
                        "siege": billet.siege,
                        "statut": billet.statut
                    })
                ca_par_jour[jour_str]["trajets"][depart_id]["ca_du_trajet"] += float(billet.montant or 0)
                ca_par_jour[jour_str]["trajets"][depart_id]["nombre_billets"] += 1
                
                # Statistiques par caissière
                if billet.agent_id and billet.agent_id in agents_dict:
                    agent_id = str(billet.agent_id)
                    if agent_id not in ca_par_jour[jour_str]["caissieres"]:
                        agent = agents_dict[billet.agent_id]
                        ca_par_jour[jour_str]["caissieres"][agent_id] = {
                            "agent_id": billet.agent_id,
                            "username": agent.username if agent else None,
                            "first_name": agent.first_name if agent else None,
                            "last_name": agent.last_name if agent else None,
                            "ca_total": 0,
                            "nombre_billets": 0
                        }
                    ca_par_jour[jour_str]["caissieres"][agent_id]["ca_total"] += float(billet.montant or 0)
                    ca_par_jour[jour_str]["caissieres"][agent_id]["nombre_billets"] += 1
                
                # Statistiques par bus
                if billet.bus_id and billet.bus_id in buses_dict:
                    bus_id = str(billet.bus_id)
                    if bus_id not in ca_par_jour[jour_str]["buses"]:
                        bus = buses_dict[billet.bus_id]
                        ca_par_jour[jour_str]["buses"][bus_id] = {
                            "bus_id": billet.bus_id,
                            "immatriculation": bus.immatriculation if bus else None,
                            "ca_total": 0,
                            "nombre_billets": 0
                        }
                    ca_par_jour[jour_str]["buses"][bus_id]["ca_total"] += float(billet.montant or 0)
                    ca_par_jour[jour_str]["buses"][bus_id]["nombre_billets"] += 1
                
                # Statistiques par destination
                if billet.destination_id and billet.destination_id in destinations_dict:
                    dest_id = str(billet.destination_id)
                    if dest_id not in ca_par_jour[jour_str]["destinations"]:
                        destination = destinations_dict[billet.destination_id]
                        ca_par_jour[jour_str]["destinations"][dest_id] = {
                            "destination_id": billet.destination_id,
                            "nom": destination.nom if destination else None,
                            "ville": destination.ville if destination else None,
                            "ca_total": 0,
                            "nombre_billets": 0
                        }
                    ca_par_jour[jour_str]["destinations"][dest_id]["ca_total"] += float(billet.montant or 0)
                    ca_par_jour[jour_str]["destinations"][dest_id]["nombre_billets"] += 1
        
        # Convertir en liste triée par date
        result = sorted(ca_par_jour.values(), key=lambda x: x["date"], reverse=True)
        
        response = {
            "periode": {
                "debut": start.isoformat(),
                "fin": end.isoformat()
            },
            "donnees_par_jour": result,
            "total_ca": sum(day["chiffre_affaires_total"] for day in result),
            "total_transactions": sum(day["nombre_transactions"] for day in result)
        }
        
        # Avertir si la limite a été atteinte
        if limite_atteinte:
            response["avertissement"] = f"Limite de 15000 billets atteinte sur {total_billets} au total. Réduisez la période pour voir tous les résultats."
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")

@router.get("/billets/jours")
def get_billets_par_jour(
    start_date: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    """
    Retourne le nombre de billets vendus par jour avec détails
    """
    # Réutiliser la même logique que chiffre-affaires mais focus sur les billets
    result = get_chiffre_affaires_par_jour(start_date, end_date, db, current_user)
    
    # Reformater pour focus billets
    for jour in result["donnees_par_jour"]:
        jour["billets_vendus"] = jour["nombre_transactions"]
    
    return result

@router.get("/trajets/jour/{date_str}")
def get_trajets_du_jour(
    date_str: str,
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    """
    Retourne tous les trajets d'un jour spécifique avec tous les détails
    Format date: YYYY-MM-DD
    Optimisé pour éviter les requêtes N+1
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # OPTIMISATION: Récupérer tous les départs en une seule requête
        departs = db.query(DepartModel).filter(
            func.date(DepartModel.date_depart) == target_date
        ).limit(300).all()  # Limite réduite pour éviter les réponses trop lourdes
        
        if not departs:
            return {
                "date": date_str,
                "nombre_trajets": 0,
                "trajets": []
            }
        
        # OPTIMISATION: Précharger toutes les données nécessaires
        bus_ids = list(set([d.bus_id for d in departs if d.bus_id]))
        ligne_ids = list(set([d.ligne_id for d in departs if d.ligne_id]))
        destination_ids = list(set([d.destination_id for d in departs if d.destination_id]))
        chauffeur_ids = list(set([d.chauffeur_id for d in departs if d.chauffeur_id]))
        depart_ids = [d.id for d in departs]
        
        buses_dict = {b.id: b for b in db.query(BusModel).filter(BusModel.id.in_(bus_ids)).all()}
        lignes_dict = {l.id: l for l in db.query(LigneModel).filter(LigneModel.id.in_(ligne_ids)).all()}
        destinations_dict = {d.id: d for d in db.query(DestinationModel).filter(DestinationModel.id.in_(destination_ids)).all()}
        chauffeurs_dict = {c.id: c for c in db.query(ChauffeurModel).filter(ChauffeurModel.id.in_(chauffeur_ids)).all()}
        
        # Charger toutes les assignations de bus
        bus_chauffeurs_dict = {}
        if bus_ids:
            assignations = db.query(BusChauffeurModel).filter(
                BusChauffeurModel.bus_id.in_(bus_ids),
                BusChauffeurModel.is_actif == True
            ).all()
            for assign in assignations:
                if assign.bus_id not in bus_chauffeurs_dict:
                    bus_chauffeurs_dict[assign.bus_id] = []
                bus_chauffeurs_dict[assign.bus_id].append(assign)
        
        # Charger tous les billets pour ces départs
        billets_dict = {}
        if depart_ids:
            billets = db.query(BilletModel).filter(BilletModel.depart_id.in_(depart_ids)).all()
            for billet in billets:
                if billet.depart_id not in billets_dict:
                    billets_dict[billet.depart_id] = []
                billets_dict[billet.depart_id].append(billet)
        
        # Charger tous les agents en une seule requête
        agent_ids = list(set([b.agent_id for b in sum(billets_dict.values(), []) if b.agent_id]))
        agents_dict = {}
        if agent_ids:
            agents = db.query(UserModel).filter(UserModel.id.in_(agent_ids)).all()
            agents_dict = {a.id: a for a in agents}
        
        trajets_detail = []
        
        for depart in departs:
            bus = buses_dict.get(depart.bus_id)
            ligne = lignes_dict.get(depart.ligne_id)
            destination = destinations_dict.get(depart.destination_id)
            chauffeur = chauffeurs_dict.get(depart.chauffeur_id)
            
            # Récupérer les chauffeurs assignés depuis le cache
            assignations = bus_chauffeurs_dict.get(depart.bus_id, [])
            chauffeurs_assignes = []
            for assignation in assignations:
                ch = chauffeurs_dict.get(assignation.chauffeur_id)
                if ch:
                    chauffeurs_assignes.append({
                        "id": ch.id,
                        "nom": ch.nom,
                        "prenom": ch.prenom,
                        "numero_permis": ch.numero_permis,
                        "type_affectation": assignation.type_affectation
                    })
            
            # Récupérer les billets depuis le cache
            billets = billets_dict.get(depart.id, [])
            
            # Calculer les statistiques des caissières
            caissieres = {}
            for billet in billets:
                if billet.agent_id and billet.agent_id in agents_dict:
                    agent = agents_dict[billet.agent_id]
                    agent_id = str(agent.id)
                    if agent_id not in caissieres:
                        caissieres[agent_id] = {
                            "agent_id": agent.id,
                            "username": agent.username,
                            "first_name": agent.first_name,
                            "last_name": agent.last_name,
                            "billets_vendus": 0,
                            "ca": 0
                        }
                    caissieres[agent_id]["billets_vendus"] += 1
                    caissieres[agent_id]["ca"] += float(billet.montant or 0)
            
            trajets_detail.append({
                "depart_id": depart.id,
                "bus": {
                    "id": bus.id if bus else None,
                    "immatriculation": bus.immatriculation if bus else None,
                    "marque": bus.marque if bus else None,
                    "modele": bus.modele if bus else None,
                    "capacite": bus.capacite if bus else None
                } if bus else None,
                "ligne": {
                    "id": ligne.id if ligne else None,
                    "numero": ligne.numero if ligne else None,
                    "point_depart": ligne.point_depart if ligne else None,
                    "point_arrivee": ligne.point_arrivee if ligne else None,
                    "distance_km": ligne.distance_km if ligne else None
                } if ligne else None,
                "destination": {
                    "id": destination.id if destination else None,
                    "nom": destination.nom if destination else None,
                    "ville": destination.ville if destination else None,
                    "tarif": float(destination.tarif) if destination and destination.tarif else None
                } if destination else None,
                "chauffeur": {
                    "id": chauffeur.id if chauffeur else None,
                    "nom": chauffeur.nom if chauffeur else None,
                    "prenom": chauffeur.prenom if chauffeur else None,
                    "numero_permis": chauffeur.numero_permis if chauffeur else None
                } if chauffeur else None,
                "chauffeurs_assignes": chauffeurs_assignes,
                "heure_depart": depart.heure_depart.strftime("%H:%M") if depart.heure_depart else None,
                "heure_arrivee_estimee": _calculate_arrival_time(depart.heure_depart, ligne.duree_minutes if ligne and ligne.duree_minutes else None),
                "date_depart": depart.date_depart.isoformat() if depart.date_depart else None,
                "places_disponibles": depart.places_disponibles,
                "prix": float(depart.prix) if depart.prix else None,
                "statut": depart.statut,
                "billets": [
                    {
                        "id": b.id,
                        "nom_client": b.nom_client,
                        "telephone_client": b.telephone_client,
                        "montant": float(b.montant or 0),
                        "mode_paiement": b.mode_paiement,
                        "siege": b.siege,
                        "statut": b.statut,
                        "date_achat": b.date_achat.isoformat() if b.date_achat else None
                    }
                    for b in billets[:500]  # Limiter à 500 billets par trajet
                ],
                "caissieres": list(caissieres.values()),
                "nombre_billets_vendus": len(billets),
                "nombre_billets_affiches": min(len(billets), 500),
                "chiffre_affaires_trajet": sum(float(b.montant or 0) for b in billets)
            })
        
        return {
            "date": date_str,
            "nombre_trajets": len(trajets_detail),
            "trajets": trajets_detail
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des trajets: {str(e)}")
