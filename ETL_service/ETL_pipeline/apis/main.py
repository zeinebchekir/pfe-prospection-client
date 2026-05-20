import sys
sys.path.insert(0, "/app")

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apis.routers.segmentation import router as segmentation_router
from apis.routers.etl_status import router as etl_status_router
from apis.routers import sync, entreprise, logs, notifications
from apis.routers.monitoring import router as monitoring_router
from apis.routers.rapport import router as rapport_router
from apis.routers.notifications import dispatch_notifications
from apis.routers.generate_leads import router as generate_leads_router
from db.database import create_tables


# ── Lifespan (remplace on_event deprecated) ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup : crée les tables + lance le dispatcher SSE."""
    create_tables()
    task = asyncio.create_task(dispatch_notifications())
    yield
    # Shutdown : annule la tâche proprement
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="ETL Scraping Service",
    description="API de consultation des données scrappées",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(sync.router,              prefix="/sync",        tags=["Sync"])
app.include_router(entreprise.router,        prefix="/entreprises", tags=["Entreprises"])
app.include_router(monitoring_router)
app.include_router(rapport_router)
app.include_router(logs.router)
app.include_router(notifications.router)
app.include_router(segmentation_router,      prefix="/segmentation", tags=["Segmentation"])
app.include_router(etl_status_router)
app.include_router(generate_leads_router)


@app.on_event("startup")
def startup():
    """Crée les tables au démarrage de FastAPI."""
    print("[STARTUP] Création des tables dans la base de données...")
    create_tables()
    print("[STARTUP] Tables prêtes.")


@app.get("/")
def root():
    return {"status": "ok", "message": "ETL Service API"}