"""
Script de génération de données complètes pour l'année 2025 et départs 2026
Génère des données réalistes pour toute l'année 2025 et des départs pour fin janvier/février 2026
"""
import os
import sys
from datetime import datetime, timedelta, time, date
import random
from sqlalchemy.orm import Session

# Définir DB_HOST avant l'import de database
if not os.getenv("DB_HOST"):
    os.environ["DB_HOST"] = "localhost"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from models import (
    User, Bus, Ligne, Destination, Chauffeur, Depart, Billet, Atelier,
    Organization, Role, BusChauffeur
)
from auth.hash_password import hash_password

# Configuration
START_DATE_2025 = datetime(2025, 1, 1)
END_DATE_2025 = datetime(2025, 12, 31)
START_DATE_2026 = datetime(2026, 1, 15)  # Fin janvier 2026
END_DATE_2026 = datetime(2026, 2, 28)  # Fin février 2026

# Heures de départ entre 4h et 22h
HEURES_DEPART = list(range(4, 23))  # 4h à 22h

# Données de base
VILLES_CAMEROUN = [
    "Douala", "Yaoundé", "Bafoussam", "Bamenda", "Garoua", 
    "Maroua", "Kribi", "Limbe", "Ebolowa", "Bertoua"
]

PRENOMS = [
    "Jean", "Pierre", "Marie", "Paul", "Sophie", "Luc", "Anne", "Michel",
    "Julie", "Thomas", "Sarah", "David", "Emma", "Nicolas", "Laura",
    "Marc", "Claire", "Philippe", "Céline", "Antoine", "Camille", "Julien",
    "Aurélie", "Romain", "Émilie", "Sébastien", "Amélie", "Vincent", "Marine",
    "Christophe", "Benoît", "Valérie", "Guillaume", "Nathalie", "Olivier"
]

NOMS = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
    "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
    "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
    "Girard", "André", "Lefevre", "Mercier", "Dupont", "Lambert", "Bonnet"
]

MARQUES_BUS = ["Mercedes", "Volvo", "Scania", "MAN", "Iveco", "Daf", "Renault"]
MODELE_BUS = {
    "Mercedes": ["Sprinter", "Tourismo", "Intouro", "Citaro"],
    "Volvo": ["9700", "9900", "B12", "B11R"],
    "Scania": ["Interlink", "Touring", "Omnibus"],
    "MAN": ["Lion's Coach", "Lion's Intercity", "RR"],
    "Iveco": ["Crossway", "Magelys", "Evadys"],
    "Daf": ["CF", "XF", "LF"],
    "Renault": ["Ares", "Agora", "Irisbus"]
}

STATUTS_BUS = ["en_service", "en_maintenance", "hors_service", "disponible"]
STATUTS_CHAUFFEUR = ["actif", "conge", "suspendu"]

MODES_PAIEMENT = ["espece", "carte", "mobile"]
STATUTS_BILLET = ["valide", "utilise", "annule", "rembourse"]

TYPES_PANNE = ["freinage", "pneus", "moteur", "électrique", "climatisation", "carrosserie", "transmission"]
GRAVITES_PANNE = ["mineure", "moyenne", "majeure", "critique"]

def generate_immatriculation(index):
    """Génère une immatriculation camerounaise"""
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    num1 = f"{random.randint(1000, 9999):04d}"
    let1 = random.choice(letters)
    let2 = random.choice(letters)
    return f"CM-{num1}-{let1}{let2}"

def generate_phone():
    """Génère un numéro de téléphone camerounais"""
    return f"2376{random.randint(10000000, 99999999)}"

def generate_qr_code():
    """Génère un code QR unique"""
    return f"QR{random.randint(1000000000, 9999999999)}"

def is_weekend(dt):
    """Vérifie si c'est un weekend"""
    return dt.weekday() >= 5

def generate_departs_for_period(db, start_date, end_date, buses, chauffeurs, lignes, destinations, agents, year_label):
    """Génère des départs pour une période donnée"""
    print(f"\n=== Génération des départs pour {year_label} ===")
    
    departs_created = 0
    billets_created = 0
    current_date = start_date
    
    # Créer un dictionnaire pour suivre les assignations bus/chauffeur par date/heure
    bus_schedule = {}  # {(bus_id, date, heure): True}
    chauffeur_schedule = {}  # {(chauffeur_id, date, heure): True}
    
    # Mapper les chauffeurs jour/nuit pour chaque bus
    bus_chauffeurs_map = {}
    for bus in buses:
        jour_chauffeurs = [c for c in chauffeurs if c.statut == "actif"]
        nuit_chauffeurs = [c for c in chauffeurs if c.statut == "actif"]
        if jour_chauffeurs and nuit_chauffeurs:
            bus_chauffeurs_map[bus.id] = {
                'jour': random.choice(jour_chauffeurs).id,
                'nuit': random.choice(nuit_chauffeurs).id
            }
    
    while current_date <= end_date:
        day_of_week = current_date.weekday()
        is_weekend_day = is_weekend(current_date)
        
        # Plus de départs le weekend
        num_departs_day = random.randint(8, 15) if is_weekend_day else random.randint(5, 12)
        
        heures_selectionnees = random.sample(HEURES_DEPART, min(num_departs_day, len(HEURES_DEPART)))
        
        for heure in sorted(heures_selectionnees):
            ligne = random.choice(lignes)
            destination = random.choice(destinations)
            
            # Trouver un bus disponible
            available_buses = [b for b in buses if b.statut in ["en_service", "disponible"]]
            if not available_buses:
                continue
            
            bus = random.choice(available_buses)
            bus_key = (bus.id, current_date.date(), heure)
            
            if bus_key in bus_schedule:
                continue
            
            # Déterminer chauffeur selon l'heure (jour: 4h-15h, nuit: 16h-22h)
            if heure < 16:
                type_affectation = "jour"
            else:
                type_affectation = "nuit"
            
            if bus.id in bus_chauffeurs_map:
                chauffeur_id = bus_chauffeurs_map[bus.id][type_affectation]
            else:
                available_chauffeurs = [c for c in chauffeurs if c.statut == "actif"]
                if not available_chauffeurs:
                    continue
                chauffeur = random.choice(available_chauffeurs)
                chauffeur_id = chauffeur.id
            
            chauffeur_key = (chauffeur_id, current_date.date(), heure)
            if chauffeur_key in chauffeur_schedule:
                continue
            
            # Créer le départ
            places_disponibles = bus.capacite - 2  # Réserver 2 places (chauffeur + assistant)
            
            depart = Depart(
                ligne_id=ligne.id,
                destination_id=destination.id,
                bus_id=bus.id,
                chauffeur_id=chauffeur_id,
                date_depart=datetime.combine(current_date.date(), time(heure, 0)),
                heure_depart=time(heure, 0),
                places_disponibles=places_disponibles,
                prix=destination.tarif,
                statut="programme" if current_date > datetime.now() else ("termine" if current_date < datetime.now() - timedelta(hours=6) else "en_cours"),
                date_creation=current_date if year_label == "2025" else datetime.now()
            )
            db.add(depart)
            db.flush()
            
            bus_schedule[bus_key] = True
            chauffeur_schedule[chauffeur_key] = True
            departs_created += 1
            
            # Pour les dates passées (2025 uniquement), créer des billets vendus
            if year_label == "2025" and current_date < datetime.now() - timedelta(hours=6):
                # Générer des ventes de billets (taux d'occupation variable)
                taux_occupation = random.uniform(0.4, 0.95) if is_weekend_day else random.uniform(0.3, 0.85)
                nb_billets = int(places_disponibles * taux_occupation)
                
                sieges_utilises = set()
                for _ in range(nb_billets):
                    siege = random.randint(1, bus.capacite)
                    while siege in sieges_utilises:
                        siege = random.randint(1, bus.capacite)
                    sieges_utilises.add(siege)
                    
                    agent = random.choice(agents)
                    mode_paiement = random.choice(MODES_PAIEMENT)
                    statut_billet = random.choices(
                        STATUTS_BILLET,
                        weights=[70, 25, 3, 2]  # Plus de billets valides/utilisés
                    )[0]
                    
                    date_achat = current_date + timedelta(
                        days=random.randint(-2, 0),
                        hours=random.randint(0, heure-1)
                    )
                    
                    billet = Billet(
                        depart_id=depart.id,
                        bus_id=bus.id,
                        destination_id=destination.id,
                        ligne_id=ligne.id,
                        chauffeur_id=chauffeur_id,
                        siege=siege,
                        agent_id=agent.id,
                        mode_paiement=mode_paiement,
                        montant=destination.tarif,
                        date_achat=date_achat,
                        statut=statut_billet,
                        code_qr=generate_qr_code(),
                        date_utilisation=date_achat + timedelta(hours=random.randint(0, 2)) if statut_billet == "utilise" else None,
                        nom_client=f"{random.choice(PRENOMS)} {random.choice(NOMS)}",
                        telephone_client=generate_phone()
                    )
                    db.add(billet)
                    billets_created += 1
            
            if departs_created % 50 == 0:
                db.commit()
                print(f"  Départs créés: {departs_created}, Billets: {billets_created}")
        
        current_date += timedelta(days=1)
    
    db.commit()
    print(f"\n✓ {year_label}: {departs_created} départs créés, {billets_created} billets créés")
    return departs_created, billets_created

def generate_maintenance_interventions(db, start_date, end_date, buses, techniciens):
    """Génère des interventions de maintenance pour la période"""
    print(f"\n=== Génération des interventions de maintenance ===")
    
    interventions_created = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Probabilité d'intervention par jour
        if random.random() < 0.15:  # 15% de chance par jour
            bus = random.choice([b for b in buses if b.statut != "hors_service"])
            if not bus:
                current_date += timedelta(days=1)
                continue
            
            type_panne = random.choice(TYPES_PANNE)
            gravite = random.choice(GRAVITES_PANNE)
            
            # Durée selon la gravité
            duree_jours = {
                "mineure": random.randint(1, 2),
                "moyenne": random.randint(2, 5),
                "majeure": random.randint(5, 10),
                "critique": random.randint(10, 20)
            }[gravite]
            
            date_entree = current_date
            date_sortie = current_date + timedelta(days=duree_jours) if random.random() < 0.8 else None
            
            technicien = random.choice(techniciens) if techniciens else None
            
            statut = "terminee" if date_sortie and date_sortie < datetime.now() else ("en_cours" if date_entree <= datetime.now() and (not date_sortie or date_sortie > datetime.now()) else "en_attente")
            
            cout = {
                "mineure": random.uniform(50, 200),
                "moyenne": random.uniform(200, 500),
                "majeure": random.uniform(500, 1500),
                "critique": random.uniform(1500, 5000)
            }[gravite]
            
            intervention = Atelier(
                bus_id=bus.id,
                technicien_id=technicien.id if technicien else None,
                date_entree=date_entree,
                date_sortie=date_sortie,
                type_panne=type_panne,
                gravite=gravite,
                description=f"Intervention {type_panne} - Gravité: {gravite}",
                pieces_remplacees=random.choice(["Filtres", "Pneus", "Freins", "Batterie", "Aucune"]),
                cout_intervention=cout,
                statut=statut,
                date_creation=date_entree
            )
            db.add(intervention)
            
            # Mettre le bus en maintenance si nécessaire
            if statut == "en_cours":
                bus.statut = "en_maintenance"
            
            interventions_created += 1
        
        if interventions_created % 20 == 0 and interventions_created > 0:
            db.commit()
        
        current_date += timedelta(days=1)
    
    db.commit()
    print(f"✓ {interventions_created} interventions créées")
    return interventions_created

def main():
    """Fonction principale"""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    try:
        print("=" * 60)
        print("GÉNÉRATION DE DONNÉES COMPLÈTES")
        print("Année 2025 (janvier-décembre) + Départs 2026 (fin jan-fév)")
        print("=" * 60)
        
        # 1. Vérifier les données de base existantes
        print("\n1. Vérification des données de base...")
        buses = db.query(Bus).all()
        chauffeurs = db.query(Chauffeur).filter(Chauffeur.statut == "actif").all()
        lignes = db.query(Ligne).filter(Ligne.statut == "active").all()
        destinations = db.query(Destination).all()
        agents = db.query(User).filter(User.role == "agent", User.is_active == True).all()
        techniciens = db.query(User).filter(User.role == "maintenance", User.is_active == True).all()
        
        if not buses or not chauffeurs or not lignes or not destinations:
            print("❌ ERREUR: Données de base manquantes!")
            print("   Veuillez d'abord exécuter seed_data.py pour créer les données de base")
            return
        
        print(f"   ✓ {len(buses)} bus disponibles")
        print(f"   ✓ {len(chauffeurs)} chauffeurs actifs")
        print(f"   ✓ {len(lignes)} lignes actives")
        print(f"   ✓ {len(destinations)} destinations")
        print(f"   ✓ {len(agents)} agents")
        print(f"   ✓ {len(techniciens)} techniciens")
        
        # 2. Générer les départs pour 2025
        departs_2025, billets_2025 = generate_departs_for_period(
            db, START_DATE_2025, END_DATE_2025, buses, chauffeurs, lignes, destinations, agents, "2025"
        )
        
        # 3. Générer les interventions de maintenance pour 2025
        interventions_2025 = generate_maintenance_interventions(
            db, START_DATE_2025, END_DATE_2025, buses, techniciens
        )
        
        # 4. Générer les départs pour fin janvier et février 2026
        departs_2026, billets_2026 = generate_departs_for_period(
            db, START_DATE_2026, END_DATE_2026, buses, chauffeurs, lignes, destinations, agents, "2026 (fin jan-fév)"
        )
        
        print("\n" + "=" * 60)
        print("RÉSUMÉ DE LA GÉNÉRATION")
        print("=" * 60)
        print(f"✓ Année 2025:")
        print(f"  - {departs_2025} départs créés")
        print(f"  - {billets_2025} billets créés")
        print(f"  - {interventions_2025} interventions de maintenance")
        print(f"\n✓ 2026 (fin janvier - février):")
        print(f"  - {departs_2026} départs créés")
        print(f"  - {billets_2026} billets créés (simulés)")
        print("\n✅ Génération terminée avec succès!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
