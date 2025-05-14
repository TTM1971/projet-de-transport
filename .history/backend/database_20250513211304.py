from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuration de la base PostgreSQL (assure-toi que ces infos correspondent à ton docker-compose)
DATABASE_URL = "postgresql://user:password@database:5432/transport_db"

# Création du moteur de connexion
engine = create_engine(DATABASE_URL)

# Session SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe de base pour les modèles
Base = declarative_base()
from sqlalchemy.orm import Session
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
