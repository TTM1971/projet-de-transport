from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import billets, pings, ateliers, auth, bus, ligne, destination, users, chauffeurs, departs, roles, organizations, parametres, sessions, audit, analytics, bus_chauffeurs, analytics_detail
from database import engine, Base
from models import (
    User, Atelier, Ping, Bus, Ligne, Destination, Billet, Chauffeur, Depart,
    Role, Permission, Session, AuditLog, PasswordResetToken, Organization,
    Parametre, Tarif
)  # Import des modèles pour création des tables
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création automatique des tables en base de données
Base.metadata.create_all(bind=engine)

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

# Configuration CORS pour permettre les requêtes depuis le frontend
# Autorise les requêtes depuis localhost (développement local) et depuis le conteneur Docker
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",  # Pour les requêtes depuis le conteneur frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des différents routeurs
app.include_router(auth.router, prefix="/auth", tags=["Authentification"])
app.include_router(users.router, prefix="/users", tags=["Gestion Utilisateurs"])
app.include_router(bus.router, prefix="/bus", tags=["Gestion Bus"])
app.include_router(ligne.router, prefix="/lignes", tags=["Gestion Lignes"])
app.include_router(destination.router, prefix="/destinations", tags=["Gestion Destinations"])
app.include_router(billets.router, prefix="/billets", tags=["Billetterie"])
app.include_router(pings.router, prefix="/pings", tags=["Suivi flotte"])
app.include_router(ateliers.router, prefix="/ateliers", tags=["Garage"])
app.include_router(chauffeurs.router, prefix="/chauffeurs", tags=["Gestion Chauffeurs"])
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
