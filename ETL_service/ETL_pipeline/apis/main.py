import sys
sys.path.insert(0, "/app")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apis.routers import sync, entreprise
from db.database import create_tables

app = FastAPI(
    title="ETL Scraping Service",
    description="API de consultation des données scrappées",
    version="1.0.0"
)

# Configuration CORS pour autoriser le frontend Vue.js à consommer l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À changer en production avec l'URL exacte du front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    """Crée les tables au démarrage de FastAPI."""
    print("Création des tables dans la base de données...")
    create_tables()

app.include_router(sync.router,        prefix="/sync",        tags=["Sync"])
app.include_router(entreprise.router, prefix="/entreprises", tags=["Entreprises"])

@app.get("/")
def root():
    return {"status": "ok", "message": "ETL Service API"}