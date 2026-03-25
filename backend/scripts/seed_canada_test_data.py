"""
Réinitialise les données d'exploitation (trajets, lignes, bus, conducteurs) et insère un jeu de test CANADA.
À la fin, crée ou met à jour les comptes de démo (admin, agent_ottawa, etc.) pour correspondre à la page de connexion.

Usage (depuis le dossier backend, avec DB accessible) :
  python scripts/seed_canada_test_data.py

Variables d'environnement : DB_HOST, DB_USER, etc. comme database.py
"""
import os
import sys
from datetime import datetime, timedelta, time, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.getenv("DB_HOST"):
    os.environ["DB_HOST"] = "localhost"

from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import (
    Billet,
    Depart,
    BusChauffeur,
    Chauffeur,
    Bus,
    Ligne,
    Destination,
    Atelier,
)
from models.pings import Ping
from models.staff_shift import StaffShift
from models.tarif import Tarif

from create_user import create_default_users


def ensure_schema_compat() -> None:
    """
    Bases créées avant l'ajout du champ chauffeurs.user_id : create_all ne modifie pas les tables existantes.
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE chauffeurs
                ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ix_chauffeurs_user_id
                ON chauffeurs (user_id);
                """
            )
        )


def clear_tables(db: Session) -> None:
    """Supprime les données métier liées aux trajets (ordre respectant les FK)."""
    db.query(Billet).delete()
    db.query(Depart).delete()
    db.query(BusChauffeur).delete()
    db.query(StaffShift).delete()
    db.query(Atelier).delete()
    db.query(Ping).delete()
    db.query(Tarif).delete()
    db.query(Chauffeur).delete()
    db.query(Bus).delete()
    db.query(Destination).delete()
    db.query(Ligne).delete()
    db.commit()
    print("✓ Anciennes données (départs, lignes, destinations, bus, chauffeurs, billets) supprimées.")


def seed_canada(db: Session) -> None:
    # --- Lignes (itinéraires de test Canada) ---
    lignes_data = [
        {
            "numero": "ON-401-E",
            "nom": "Ottawa – Toronto Express",
            "point_depart": "Ottawa, ON (Gare centrale)",
            "point_arrivee": "Toronto, ON (Union Station Bus)",
            "distance_km": 450.0,
            "duree_minutes": 300,
            "tarif": 59.99,
        },
        {
            "numero": "QC-20-N",
            "nom": "Montréal – Québec",
            "point_depart": "Montréal, QC (Gare d'autocars)",
            "point_arrivee": "Québec, QC (Gare du Palais)",
            "distance_km": 255.0,
            "duree_minutes": 180,
            "tarif": 42.5,
        },
        {
            "numero": "BC-1-S",
            "nom": "Vancouver – Victoria",
            "point_depart": "Vancouver, BC (Pacific Central)",
            "point_arrivee": "Victoria, BC (Capital City Station)",
            "distance_km": 115.0,
            "duree_minutes": 240,
            "tarif": 38.0,
        },
    ]
    lignes = []
    for ld in lignes_data:
        li = Ligne(
            numero=ld["numero"],
            nom=ld["nom"],
            point_depart=ld["point_depart"],
            point_arrivee=ld["point_arrivee"],
            distance_km=ld["distance_km"],
            duree_minutes=ld["duree_minutes"],
            tarif=ld["tarif"],
            statut="active",
        )
        db.add(li)
        lignes.append(li)
    db.flush()

    # --- Destinations (terminus / tarif CAD) — pas de FK ligne dans le modèle actuel ---
    dest_specs = [
        ("Toronto Union Station", "Toronto", 59.99),
        ("Québec Gare du Palais", "Québec", 42.5),
        ("Victoria Capital Terminal", "Victoria", 38.0),
    ]
    destinations = []
    for nom, ville, prix in dest_specs:
        d = Destination(
            nom=nom,
            ville=ville,
            tarif=prix,
            duree_estimee_minutes=180,
            description="Données de test — Canada (CAD)",
        )
        db.add(d)
        destinations.append(d)
    db.flush()

    # --- Autobus (immatriculations de test style provincial) ---
    buses_data = [
        ("ON-482-AB1", "Motor Coach", "Prevost H3-45", 55, "en_service"),
        ("ON-482-AB2", "Motor Coach", "Prevost H3-45", 55, "en_service"),
        ("QC-901-MTL", "Autocar", "Motor Coach", 50, "en_service"),
        ("BC-4K2-77A", "Coach", "Van Hool CX45", 52, "disponible"),
    ]
    buses = []
    for imm, marque, modele, cap, stat in buses_data:
        b = Bus(
            immatriculation=imm,
            marque=marque,
            modele=modele,
            capacite=cap,
            statut=stat,
            annee=2022,
        )
        db.add(b)
        buses.append(b)
    db.flush()

    # --- Conducteurs (permis de test non officiels, format provincial simplifié) ---
    chauffeurs_data = [
        ("Tremblay", "Marc", "ON-D-12345678901", "Ottawa"),
        ("Ouellette", "Sophie", "ON-D-99887766554", "Ottawa"),
        ("Gagnon", "Jean", "QC-5-12-3456-78", "Montréal"),
        ("MacDonald", "Alex", "BC-9-8765432", "Vancouver"),
        ("Singh", "Harjit", "BC-9-7654321", "Vancouver"),
    ]
    chs = []
    for nom, prenom, permis, ville in chauffeurs_data:
        c = Chauffeur(
            nom=nom,
            prenom=prenom,
            numero_permis=permis,
            ville=ville,
            telephone="+1-416-555-0100",
            statut="actif",
        )
        db.add(c)
        chs.append(c)
    db.flush()

    # --- Départs (14 prochains jours) : en alternance les 3 corridors ---
    ligne_dest_map = [
        (lignes[0], destinations[0]),
        (lignes[1], destinations[1]),
        (lignes[2], destinations[2]),
    ]
    today = date.today()
    heures = [time(7, 30), time(12, 0), time(17, 30)]
    idx = 0
    for day_offset in range(14):
        dday = today + timedelta(days=day_offset)
        for h in heures:
            ligne, dest = ligne_dest_map[idx % 3]
            bus = buses[idx % len(buses)]
            ch = chs[idx % len(chs)]
            dt = datetime.combine(dday, h)
            dep = Depart(
                ligne_id=ligne.id,
                destination_id=dest.id,
                bus_id=bus.id,
                chauffeur_id=ch.id,
                date_depart=dt,
                heure_depart=h,
                places_disponibles=max(10, bus.capacite - 4),
                prix=float(dest.tarif),
                statut="programme",
            )
            db.add(dep)
            idx += 1

    db.commit()
    print("✓ Données Canada insérées : lignes, destinations, bus, conducteurs, départs (14 jours).")


def main():
    Base.metadata.create_all(bind=engine)
    ensure_schema_compat()
    db = SessionLocal()
    try:
        print("Réinitialisation des trajets / itinéraires (Canada test)…")
        clear_tables(db)
        seed_canada(db)
    finally:
        db.close()

    create_default_users()


if __name__ == "__main__":
    main()
