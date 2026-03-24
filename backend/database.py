import os

# Aide libpq sous Windows
os.environ.setdefault("PGCLIENTENCODING", "UTF8")

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# psycopg3 en priorité (meilleur UTF-8 sous Windows) ; repli psycopg2 (images Docker non reconstruites)
try:
    import psycopg  # noqa: F401

    _PSYCOPG_DRIVER = "postgresql+psycopg"
    _USE_PSYCOPG3 = True
except ImportError:
    _PSYCOPG_DRIVER = "postgresql+psycopg2"
    _USE_PSYCOPG3 = False

# Configuration de la base PostgreSQL
# Utilise 'database' pour Docker, 'localhost' pour le développement local
DB_HOST = os.getenv("DB_HOST", "database")  # 'database' pour Docker, 'localhost' pour local
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "transport_db")
DB_PORT = os.getenv("DB_PORT", "5432")


def _db_port() -> int:
    try:
        return int(DB_PORT)
    except (TypeError, ValueError):
        return 5432


def _build_database_url() -> URL:
    """URL pour SQLAlchemy (échappe correctement le mot de passe)."""
    return URL.create(
        drivername=_PSYCOPG_DRIVER,
        username=DB_USER or None,
        password=DB_PASSWORD if DB_PASSWORD is not None else "",
        host=DB_HOST or None,
        port=_db_port(),
        database=DB_NAME or None,
    )


DATABASE_URL = _build_database_url()

# Arguments de connexion selon le pilote
if _USE_PSYCOPG3:
    _CONNECT_ARGS = {
        "connect_timeout": 15,
        "options": "-c statement_timeout=300000",
    }
else:
    _CONNECT_ARGS = {
        "connect_timeout": 15,
        "options": "-c statement_timeout=300000",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }

engine = create_engine(
    DATABASE_URL,
    pool_size=15,
    max_overflow=25,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=60,
    echo=False,
    connect_args=_CONNECT_ARGS,
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
        db.rollback()  # Rollback en cas d'exception
        raise
    finally:
        db.close()  # Fermeture propre de la session
