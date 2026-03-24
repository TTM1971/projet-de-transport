import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from middleware.security import (
    ALLOWED_ORIGINS,
    OriginEnforcementMiddleware,
    SecurityHeadersMiddleware,
)
from routes import billets, pings, ateliers, auth, bus, ligne, destination, users, chauffeurs, departs, roles, organizations, parametres, sessions, audit, analytics, bus_chauffeurs, analytics_detail, chauffeur_portal, planning_staff, villes
from database import engine, Base
from sqlalchemy import text
from models import (
    User, Atelier, Ping, Bus, Ligne, Destination, Billet, Chauffeur, Depart,
    Role, Permission, Session, AuditLog, PasswordResetToken, Organization,
    Parametre, Tarif, StaffShift,
)  # Import des modèles pour création des tables
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création automatique des tables en base de données
Base.metadata.create_all(bind=engine)


def ensure_schema_compat() -> None:
    """Ajoute les colonnes manquantes sur bases déjà existantes."""
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS ville VARCHAR;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_ville ON users (ville);"))
        conn.execute(text("ALTER TABLE chauffeurs ADD COLUMN IF NOT EXISTS ville VARCHAR;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chauffeurs_ville ON chauffeurs (ville);"))


ensure_schema_compat()

app = FastAPI()

# Middleware pour logger les requêtes et erreurs  
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    logger.info(f"{request.method} {request.url}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        if process_time > 5.0:  # Logger les requêtes qui prennent plus de 5 secondes
            logger.warning(f"Slow request: {request.method} {request.url} took {process_time:.2f}s")
        if response.status_code >= 400:
            logger.warning(f"Response: {response.status_code} for {request.method} {request.url} (took {process_time:.2f}s)")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Error: {str(e)} after {process_time:.2f}s for {request.method} {request.url}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Erreur interne du serveur"}
        )

# Handler pour les erreurs de validation Pydantic
from fastapi.exceptions import RequestValidationError
from fastapi import status as http_status

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.method} {request.url}: {exc.errors()}")
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8') if body_bytes else "No body"
        logger.error(f"Body received: {body_str[:500]}")
    except Exception as e:
        logger.error(f"Could not read body: {e}")
    
    return JSONResponse(
        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

# CORS : origines autorisées = variable d’environnement CORS_ORIGINS (voir middleware/security.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["Content-Type"],
)

# En-têtes anti-XSS / clickjacking + contrôle d’origine optionnel (anti-CSRF navigateur)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(OriginEnforcementMiddleware)

# Host autorisés (production) — ajouté en dernier pour être exécuté en premier sur la requête
_trusted_hosts = os.getenv("TRUSTED_HOSTS", "").strip()
if _trusted_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[h.strip() for h in _trusted_hosts.split(",") if h.strip()],
    )

# Inclusion des différents routeurs
app.include_router(auth.router, prefix="/auth", tags=["Authentification"])
app.include_router(users.router, prefix="/users", tags=["Gestion Utilisateurs"])
app.include_router(bus.router, prefix="/bus", tags=["Gestion Bus"])
app.include_router(ligne.router, prefix="/lignes", tags=["Gestion Lignes"])
app.include_router(destination.router, prefix="/destinations", tags=["Gestion Destinations"])
app.include_router(villes.router, prefix="/villes", tags=["Gestion Villes"])
app.include_router(billets.router, prefix="/billets", tags=["Billetterie"])
app.include_router(pings.router, prefix="/pings", tags=["Suivi flotte"])
app.include_router(ateliers.router, prefix="/ateliers", tags=["Garage"])
app.include_router(chauffeurs.router, prefix="/chauffeurs", tags=["Gestion Chauffeurs"])
app.include_router(chauffeur_portal.router, prefix="/chauffeur", tags=["Espace Chauffeur"])
app.include_router(planning_staff.router, prefix="/planning", tags=["Planification équipe"])
app.include_router(departs.router, prefix="/departs", tags=["Gestion Départs"])
app.include_router(roles.router, prefix="/roles", tags=["Gestion Rôles & Permissions"])
app.include_router(organizations.router, prefix="/organizations", tags=["Gestion Organisations"])
app.include_router(parametres.router, prefix="/parametres", tags=["Paramétrage"])
app.include_router(sessions.router, prefix="/auth/sessions", tags=["Sessions"])
app.include_router(audit.router, prefix="/admin/audit", tags=["Audit"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Statistiques"])
app.include_router(analytics_detail.router, prefix="/analytics/detail", tags=["Analytics Détails"])
app.include_router(bus_chauffeurs.router, prefix="/bus-chauffeurs", tags=["Assignations Bus-Chauffeurs"])

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API SmartTransCamer - Système de gestion de transport collectif!"}
