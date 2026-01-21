"""
Script de génération de données de test réalistes sur 30 jours
Pour alimenter les dashboards avec des graphiques interactifs
"""
import os
import sys
from datetime import datetime, timedelta, time
import random
from sqlalchemy.orm import Session

# Définir DB_HOST avant l'import de database
# Utiliser localhost par défaut si on exécute en dehors de Docker
if not os.getenv("DB_HOST"):
    os.environ["DB_HOST"] = "localhost"

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
import os

# Forcer l'utilisation de localhost si l'env var n'est pas définie
if not os.getenv("DB_HOST"):
    os.environ["DB_HOST"] = "localhost"
from models import (
    User, Bus, Ligne, Destination, Chauffeur, Depart, Billet, Atelier,
    Organization, Role
)
from auth.hash_password import hash_password

# Configuration
START_DATE = datetime.now() - timedelta(days=30)  # 30 derniers jours
DAYS_TO_GENERATE = 30

# Noms et données de test
VILLES_CAMEROUN = [
    "Douala", "Yaoundé", "Bafoussam", "Bamenda", "Garoua", 
    "Maroua", "Kribi", "Limbe", "Ebolowa", "Bertoua"
]

PRENOMS = [
    "Jean", "Pierre", "Marie", "Paul", "Sophie", "Luc", "Anne", "Michel",
    "Julie", "Thomas", "Sarah", "David", "Emma", "Nicolas", "Laura",
    "Marc", "Claire", "Philippe", "Céline", "Antoine", "Camille", "Julien",
    "Aurélie", "Romain", "Émilie", "Sébastien", "Amélie", "Vincent", "Marine",
    "Christophe", "Benoît", "Valérie", "Guillaume", "Nathalie", "Olivier",
    "Isabelle", "François", "Patricia", "Jérôme", "Sylvie", "Maxime", "Caroline",
    "Alexandre", "Cécile", "Fabien", "Élodie", "Julien", "Karine", "Bertrand",
    "Agnès", "Cédric", "Véronique", "Frédéric", "Laurence", "Grégoire", "Stéphanie"
]

NOMS = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
    "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
    "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
    "Girard", "André", "Lefevre", "Mercier", "Dupont", "Lambert", "Bonnet",
    "François", "Martinez", "Legrand", "Garnier", "Faure", "Rousseau",
    "Blanc", "Guerin", "Muller", "Henry", "Roussel", "Nicolas", "Perrin",
    "Morin", "Mathieu", "Clement", "Gauthier", "Dumont", "Lopez", "Fontaine",
    "Chevalier", "Robin", "Masson", "Sanchez", "Gerard", "Nguyen", "Boyer"
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
    """Génère une immatriculation camerounaise (format: CM-XXXX-XX)"""
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    num1 = f"{random.randint(100, 9999):04d}"
    let1 = random.choice(letters)
    let2 = random.choice(letters)
    return f"CM-{num1}-{let1}{let2}"

def generate_phone():
    """Génère un numéro de téléphone camerounais"""
    prefixes = ["237", "+237"]
    prefix = random.choice(prefixes)
    number = f"{random.randint(600000000, 699999999)}"
    return f"{prefix}{number}"

def generate_email(username, first_name, last_name, domain="transport.cm"):
    """Génère un email unique basé sur le username"""
    # Utiliser le username pour garantir l'unicité
    return f"{username}@{domain}"

def generate_planning_chauffeur(chauffeur_id, start_date, days, all_departs):
    """Génère un planning pour un chauffeur (évite les chevauchements)"""
    planning = []
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        # Générer 1-3 départs par jour pour ce chauffeur
        num_departs = random.randint(1, 3)
        heures = []
        for _ in range(num_departs):
            heure = random.choice([6, 8, 10, 12, 14, 16, 18, 20])
            if heure not in heures:
                heures.append(heure)
        
        for heure in sorted(heures):
            planning.append({
                'chauffeur_id': chauffeur_id,
                'date': current_date.date(),
                'heure': heure
            })
    return planning

def generate_planning_bus(bus_id, start_date, days, all_departs):
    """Génère un planning pour un bus (évite les chevauchements)"""
    planning = []
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        # Générer 1-4 départs par jour pour ce bus
        num_departs = random.randint(1, 4)
        heures = []
        for _ in range(num_departs):
            heure = random.choice([6, 8, 10, 12, 14, 16, 18, 20])
            if heure not in heures:
                heures.append(heure)
        
        for heure in sorted(heures):
            planning.append({
                'bus_id': bus_id,
                'date': current_date.date(),
                'heure': heure
            })
    return planning

def seed_data():
    """Génère toutes les données de test"""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    try:
        print("=== Début de la génération de données ===")
        
        # 1. Récupérer ou créer les rôles de base
        roles_map = {}
        for role_name in ['admin', 'gestionnaire', 'agent', 'maintenance']:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=f"Rôle {role_name}", is_system=True)
                db.add(role)
                db.commit()
                db.refresh(role)
            roles_map[role_name] = role
        
        # 2. Créer des organisations
        print("\n1. Création des organisations...")
        organizations = []
        org_names = ["Transport Cameroun SA", "Agence Douala", "Agence Yaoundé", "Gare Centrale"]
        for org_name in org_names:
            org = db.query(Organization).filter(Organization.name == org_name).first()
            if not org:
                org = Organization(
                    name=org_name,
                    type="compagnie" if "Transport" in org_name else "agence",
                    city=random.choice(VILLES_CAMEROUN[:3]),
                    is_active=True
                )
                db.add(org)
                organizations.append(org)
        db.commit()
        
        # 3. Créer les utilisateurs
        print("\n2. Création des utilisateurs...")
        users_map = {}
        
        # Admin
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                hashed_password=hash_password("admin123"),
                role="admin",
                first_name="Super",
                last_name="Admin",
                email="admin@transport.cm",
                phone=generate_phone(),
                is_active=True,
                created_at=START_DATE - timedelta(days=365)
            )
            db.add(admin)
        users_map['admin'] = admin
        
        # 10 Gestionnaires
        gestionnaires = []
        for i in range(1, 11):
            username = f"gest{i:02d}"
            user = db.query(User).filter(User.username == username).first()
            if not user:
                first_name = random.choice(PRENOMS)
                last_name = random.choice(NOMS)
                user = User(
                    username=username,
                    hashed_password=hash_password("password123"),
                    role="gestionnaire",
                    first_name=first_name,
                    last_name=last_name,
                    email=generate_email(username, first_name, last_name),
                    phone=generate_phone(),
                    is_active=True,
                    created_at=START_DATE - timedelta(days=random.randint(60, 300)),
                    organization_id=organizations[0].id if organizations else None
                )
                db.add(user)
            gestionnaires.append(user)
        
        # 25 Agents
        agents = []
        for i in range(1, 26):
            username = f"agent{i:02d}"
            user = db.query(User).filter(User.username == username).first()
            if not user:
                first_name = random.choice(PRENOMS)
                last_name = random.choice(NOMS)
                user = User(
                    username=username,
                    hashed_password=hash_password("password123"),
                    role="agent",
                    first_name=first_name,
                    last_name=last_name,
                    email=generate_email(username, first_name, last_name),
                    phone=generate_phone(),
                    is_active=True,
                    created_at=START_DATE - timedelta(days=random.randint(30, 180)),
                    organization_id=random.choice(organizations).id if organizations else None
                )
                db.add(user)
            agents.append(user)
        
        # 15 Techniciens Maintenance
        techniciens = []
        for i in range(1, 16):
            username = f"tech{i:02d}"
            user = db.query(User).filter(User.username == username).first()
            if not user:
                first_name = random.choice(PRENOMS)
                last_name = random.choice(NOMS)
                user = User(
                    username=username,
                    hashed_password=hash_password("password123"),
                    role="maintenance",
                    first_name=first_name,
                    last_name=last_name,
                    email=generate_email(username, first_name, last_name),
                    phone=generate_phone(),
                    is_active=True,
                    created_at=START_DATE - timedelta(days=random.randint(30, 200))
                )
                db.add(user)
            techniciens.append(user)
        
        db.commit()
        print(f"✓ {len(gestionnaires)} gestionnaires créés")
        print(f"✓ {len(agents)} agents créés")
        print(f"✓ {len(techniciens)} techniciens créés")
        
        # 4. Créer 120 Chauffeurs
        print("\n3. Création des 120 chauffeurs...")
        chauffeurs = []
        for i in range(1, 121):
            chauffeur = db.query(Chauffeur).filter(Chauffeur.numero_permis == f"PERM-{i:04d}").first()
            if not chauffeur:
                first_name = random.choice(PRENOMS)
                last_name = random.choice(NOMS)
                chauffeur = Chauffeur(
                    nom=last_name,
                    prenom=first_name,
                    telephone=generate_phone(),
                    email=generate_email(username, first_name, last_name),
                    numero_permis=f"PERM-{i:04d}",
                    statut=random.choice(STATUTS_CHAUFFEUR),
                    date_embauche=START_DATE - timedelta(days=random.randint(90, 730))
                )
                db.add(chauffeur)
            chauffeurs.append(chauffeur)
        db.commit()
        print(f"✓ {len(chauffeurs)} chauffeurs créés")
        
        # 5. Créer 8 Destinations/Villes
        print("\n4. Création des 8 destinations...")
        destinations = []
        villes_selectionnees = VILLES_CAMEROUN[:8]
        for ville in villes_selectionnees:
            dest = db.query(Destination).filter(Destination.nom == ville).first()
            if not dest:
                dest = Destination(
                    nom=ville,
                    ville=ville,
                    adresse=f"Gare centrale, {ville}",
                    tarif=random.uniform(5.0, 50.0),  # Tarifs en EUR (seront convertis en CAD à l'affichage)
                    duree_estimee_minutes=random.randint(30, 480),
                    description=f"Terminal de transport de {ville}"
                )
                db.add(dest)
            destinations.append(dest)
        db.commit()
        print(f"✓ {len(destinations)} destinations créées")
        
        # 6. Créer 18 Lignes
        print("\n5. Création des 18 lignes...")
        lignes = []
        ligne_num = 1
        for i, origine in enumerate(destinations[:6]):
            for j, destination in enumerate(destinations):
                if origine.id != destination.id and ligne_num <= 18:
                    ligne = db.query(Ligne).filter(
                        Ligne.point_depart == origine.nom,
                        Ligne.point_arrivee == destination.nom
                    ).first()
                    if not ligne:
                        distance = random.randint(50, 800)
                        duree = distance // random.randint(40, 80)  # ~1h pour 60km
                        ligne = Ligne(
                            numero=f"L{ligne_num:02d}",
                            nom=f"{origine.nom} - {destination.nom}",
                            point_depart=origine.nom,
                            point_arrivee=destination.nom,
                            distance_km=distance,
                            duree_minutes=duree,
                            tarif=random.uniform(5.0, 50.0),  # Tarif par défaut (sera remplacé par destination.tarif)
                            statut="active"
                        )
                        db.add(ligne)
                    lignes.append(ligne)
                    ligne_num += 1
        db.commit()
        print(f"✓ {len(lignes)} lignes créées")
        
        # 7. Créer 60 Bus
        print("\n6. Création des 60 bus...")
        buses = []
        for i in range(1, 61):
            immat = generate_immatriculation(i)
            bus = db.query(Bus).filter(Bus.immatriculation == immat).first()
            if not bus:
                marque = random.choice(MARQUES_BUS)
                modele = random.choice(MODELE_BUS[marque])
                annee = random.randint(2015, 2024)
                capacite = random.choice([40, 45, 50, 55, 60])
                
                # Bus anciens plus à risque de pannes
                age = 2024 - annee
                if age > 8:
                    statut_prob = {"en_service": 0.4, "en_maintenance": 0.3, "hors_service": 0.2, "disponible": 0.1}
                elif age > 5:
                    statut_prob = {"en_service": 0.6, "en_maintenance": 0.2, "hors_service": 0.1, "disponible": 0.1}
                else:
                    statut_prob = {"en_service": 0.8, "en_maintenance": 0.1, "hors_service": 0.05, "disponible": 0.05}
                
                statut = random.choices(
                    list(statut_prob.keys()),
                    weights=list(statut_prob.values())
                )[0]
                
                bus = Bus(
                    immatriculation=immat,
                    marque=marque,
                    modele=modele,
                    capacite=capacite,
                    annee=annee,
                    statut=statut,
                    date_achat=datetime(annee, 1, 1)
                )
                db.add(bus)
            buses.append(bus)
        db.commit()
        print(f"✓ {len(buses)} bus créés")
        
        # 8. Générer les départs et billets sur 30 jours
        print("\n7. Génération des départs sur 30 jours...")
        all_departs = []
        bus_assignments = {}  # {bus_id: {date: [heures]}}
        chauffeur_assignments = {}  # {chauffeur_id: {date: [heures]}}
        
        for day in range(DAYS_TO_GENERATE):
            current_date = START_DATE + timedelta(days=day)
            is_weekend = current_date.weekday() >= 5  # Samedi = 5, Dimanche = 6
            
            # Plus de départs le weekend
            num_departs_par_ligne = random.randint(4, 8) if is_weekend else random.randint(2, 5)
            
            for ligne in lignes:
                for _ in range(num_departs_par_ligne):
                    # Choisir un bus disponible
                    available_buses = [b for b in buses if b.statut in ["en_service", "disponible"]]
                    if not available_buses:
                        continue
                    
                    bus = random.choice(available_buses)
                    
                    # Vérifier que le bus n'est pas déjà assigné à cette heure
                    heure = random.choice([6, 8, 10, 12, 14, 16, 18, 20])
                    bus_key = f"{bus.id}_{current_date.date()}_{heure}"
                    
                    # Choisir un chauffeur disponible
                    available_chauffeurs = [c for c in chauffeurs if c.statut == "actif"]
                    if not available_chauffeurs:
                        continue
                    
                    chauffeur = random.choice(available_chauffeurs)
                    
                    # Choisir une destination pour cette ligne (point d'arrivée de la ligne)
                    destination = None
                    for d in destinations:
                        if d.nom == ligne.point_arrivee:
                            destination = d
                            break
                    if not destination:
                        # Si pas trouvée, prendre une destination aléatoire différente du point de départ
                        available_dests = [d for d in destinations if d.nom != ligne.point_depart]
                        if available_dests:
                            destination = random.choice(available_dests)
                        else:
                            destination = destinations[0] if destinations else None
                    
                    if not destination:
                        continue  # Pas de destination disponible, passer au suivant
                    
                    # Récupérer le tarif de la destination
                    tarif_dest = destination.tarif
                    
                    date_depart = datetime.combine(current_date.date(), time(heure, 0))
                    heure_depart = time(heure, 0)
                    
                    # Capacité initiale = capacité bus - 2 (chauffeur + assistant)
                    capacite_initiale = bus.capacite - 2
                    
                    depart = Depart(
                        ligne_id=ligne.id,
                        destination_id=destination.id,
                        bus_id=bus.id,
                        chauffeur_id=chauffeur.id,
                        date_depart=date_depart,
                        heure_depart=heure_depart,
                        places_disponibles=capacite_initiale,
                        prix=tarif_dest,
                        statut=random.choice(["programme", "termine", "en_cours"])
                    )
                    db.add(depart)
                    db.flush()  # Pour obtenir l'ID
                    all_departs.append(depart)
                    
                    # Générer des billets pour ce départ
                    taux_occupation = random.uniform(0.5, 0.95) if is_weekend else random.uniform(0.3, 0.8)
                    nb_billets = min(int(capacite_initiale * taux_occupation), capacite_initiale)
                    
                    # Quelques annulations
                    nb_annulations = random.randint(0, max(1, int(nb_billets * 0.1)))
                    nb_billets_valides = nb_billets - nb_annulations
                    
                    for seat in range(1, nb_billets_valides + 1):
                        agent = random.choice(agents)
                        mode_paiement = random.choice(MODES_PAIEMENT)
                        
                        billet = Billet(
                            depart_id=depart.id,
                            bus_id=bus.id,
                            destination_id=destination.id,
                            ligne_id=ligne.id,
                            chauffeur_id=chauffeur.id,
                            siege=seat,
                            agent_id=agent.id,
                            mode_paiement=mode_paiement,
                            montant=tarif_dest,
                            date_achat=date_depart - timedelta(hours=random.randint(1, 72)),
                            statut=random.choices(
                                ["valide", "utilise"],
                                weights=[0.3, 0.7]
                            )[0],
                            code_qr=f"QR-{depart.id}-{seat}-{random.randint(10000, 99999)}-{int(datetime.utcnow().timestamp() * 1000) % 10000}",
                            nom_client=f"{random.choice(PRENOMS)} {random.choice(NOMS)}",
                            telephone_client=generate_phone()
                        )
                        db.add(billet)
                    
                    # Annulations
                    for _ in range(nb_annulations):
                        agent = random.choice(agents)
                        billet = Billet(
                            depart_id=depart.id,
                            bus_id=bus.id,
                            destination_id=destination.id,
                            ligne_id=ligne.id,
                            chauffeur_id=chauffeur.id,
                            siege=random.randint(1, capacite_initiale),
                            agent_id=agent.id,
                            mode_paiement=random.choice(MODES_PAIEMENT),
                            montant=tarif_dest,
                            date_achat=date_depart - timedelta(hours=random.randint(1, 72)),
                            statut=random.choice(["annule", "rembourse"]),
                            code_qr=f"QR-{depart.id}-CANCEL-{random.randint(10000, 99999)}-{int(datetime.utcnow().timestamp() * 1000) % 10000}",
                            nom_client=f"{random.choice(PRENOMS)} {random.choice(NOMS)}",
                            telephone_client=generate_phone()
                        )
                        db.add(billet)
                    
                    # Mettre à jour les places disponibles
                    depart.places_disponibles = capacite_initiale - nb_billets_valides
        
        db.commit()
        print(f"✓ {len(all_departs)} départs créés")
        
        # 9. Générer les interventions de maintenance
        print("\n8. Génération des interventions de maintenance...")
        interventions = []
        
        # Bus anciens et chauffeurs avec style de conduite "agressif" ont plus de risques
        bus_anciens = [b for b in buses if (2024 - b.annee) > 7]
        chauffeurs_risque = random.sample(chauffeurs, len(chauffeurs) // 4)  # 25% des chauffeurs
        
        for day in range(DAYS_TO_GENERATE):
            current_date = START_DATE + timedelta(days=day)
            
            # Probabilité d'incident par jour (plus élevée pour bus anciens)
            if random.random() < 0.15:  # 15% de chance d'incident par jour
                # Choisir un bus (les anciens ont plus de risques)
                if random.random() < 0.6 and bus_anciens:
                    bus_incident = random.choice(bus_anciens)
                else:
                    bus_incident = random.choice([b for b in buses if b.statut != "hors_service"])
                
                type_panne = random.choice(TYPES_PANNE)
                gravite = random.choice(GRAVITES_PANNE)
                
                # Technicien assigné
                technicien = random.choice(techniciens)
                
                # Durée d'intervention selon la gravité
                duree_intervention = {
                    "mineure": random.randint(1, 4),
                    "moyenne": random.randint(4, 12),
                    "majeure": random.randint(12, 48),
                    "critique": random.randint(48, 120)
                }[gravite]
                
                date_entree = current_date + timedelta(hours=random.randint(6, 18))
                date_sortie = date_entree + timedelta(hours=duree_intervention)
                
                intervention = Atelier(
                    bus_id=bus_incident.id,
                    technicien_id=technicien.id,
                    date_entree=date_entree,
                    date_sortie=date_sortie if date_sortie < datetime.now() else None,
                    type_panne=type_panne,
                    gravite=gravite,
                    description=f"Intervention {type_panne} - Gravité: {gravite}",
                    cout_intervention=random.uniform(50, 5000),  # En EUR
                    pieces_remplacees=random.choice(["Filtres", "Pneus", "Freins", "Batterie", "Aucune"]),
                    statut="terminee" if date_sortie and date_sortie < datetime.now() else "en_cours"
                )
                db.add(intervention)
                interventions.append(intervention)
                
                # Mettre le bus en maintenance si ce n'est pas déjà fait
                if bus_incident.statut == "en_service":
                    bus_incident.statut = "en_maintenance"
        
        db.commit()
        print(f"✓ {len(interventions)} interventions de maintenance créées")
        
        print("\n=== Génération terminée avec succès ===")
        print(f"Total départs: {len(all_departs)}")
        print(f"Total billets: {db.query(Billet).count()}")
        print(f"Total interventions: {len(interventions)}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
