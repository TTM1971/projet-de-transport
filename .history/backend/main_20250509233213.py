from fastapi import FastAPI
from routes import billets, pings, ateliers, auth

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Authentification"])
app.include_router(billets.router, prefix="/billets", tags=["Billetterie"])
app.include_router(pings.router, prefix="/pings", tags=["Suivi flotte"])
app.include_router(ateliers.router, prefix="/ateliers", tags=["Garage"])

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API du transport collectif!"}
