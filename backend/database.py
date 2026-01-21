from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

# Configuration de la base PostgreSQL
# Utilise 'database' pour Docker, 'localhost' pour le développement local
DB_HOST = os.getenv("DB_HOST", "database")  # 'database' pour Docker, 'localhost' pour local
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "transport_db")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Création du moteur de connexion avec pool de connexions optimisé
# Configuration améliorée pour éviter les erreurs "Broken pipe"
engine = create_engine(
    DATABASE_URL,
    pool_size=15,  # Nombre de connexions à garder ouvertes (augmenté)
    max_overflow=25,  # Nombre de connexions supplémentaires possibles (augmenté)
    pool_pre_ping=True,  # Vérifier que les connexions sont valides avant utilisation
    pool_recycle=1800,  # Recycler les connexions après 30 minutes (réduit pour éviter les connexions mortes)
    pool_timeout=60,  # Timeout pour obtenir une connexion du pool (secondes, augmenté)
    echo=False,  # Mettre à True pour voir les requêtes SQL dans les logs
    connect_args={
        "connect_timeout": 15,  # Timeout de connexion initial (secondes, augmenté)
        "keepalives": 1,  # Activer keepalive pour détecter les connexions mortes
        "keepalives_idle": 30,  # Secondes d'inactivité avant d'envoyer un keepalive
        "keepalives_interval": 10,  # Intervalle entre les keepalives (secondes)
        "keepalives_count": 5,  # Nombre de keepalives manqués avant de considérer la connexion morte
        "options": "-c statement_timeout=300000"  # Timeout de 5 minutes pour les requêtes longues
    }
)

# Session SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe de base pour les modèles
Base = declarative_base()
from sqlalchemy.orm import Session
from fastapi import Depends

def get_db():
    """
    Dépendance FastAPI pour obtenir une session de base de données.
    La session est automatiquement fermée après utilisation grâce au finally.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Commit automatique si pas d'exception
    except Exception:
        db.rollback()  # Rollback en cas d'erreur
        raise
    finally:
        db.close()  # Fermeture propre de la session
