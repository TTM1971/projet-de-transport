from fastapi import FastAPI
from routes import billets, pings, ateliers, auth
from database import engine, Base
from models import user, ping, atelier  # Ajoute ici tous les modèles que tu veux inclure

# Création automatique des tables en base de données
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Inclusion des différents routeurs
app.include_router(auth.router, prefix="/auth", tags=["Authentification"])
app.include_router(billets.router, prefix="/billets", tags=["Billetterie"])
app.include_router(pings.router, prefix="/pings", tags=["Suivi flotte"])
app.include_router(ateliers.router, prefix="/ateliers", tags=["Garage"])

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API du transport collectif!"}
