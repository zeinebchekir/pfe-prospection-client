import sys
sys.path.insert(0, "/app")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apis.routers import sync, entreprise 
from apis.routers.monitoring import router as monitoring_router
from db.database import create_tables
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge, Counter, Histogram
import psutil
from apis.routers.rapport import router as rapport_router
from apis.routers.segmentation import router as segmentation_router
app = FastAPI(
    title="ETL Scraping Service",
    description="API de consultation des données scrappées",
    version="1.0.0"
)

# Configuration CORS pour autoriser tous les frontend à consommer l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
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
app.include_router(monitoring_router)
app.include_router(rapport_router)
app.include_router(segmentation_router, prefix="/segmentation", tags=["Segmentation"])


etl_task_cpu    = Gauge('etl_task_cpu_percent',    'CPU usage per task',    ['dag_id','task_id'])
etl_task_ram    = Gauge('etl_task_ram_percent',    'RAM usage per task',    ['dag_id','task_id'])
etl_task_disk   = Gauge('etl_task_disk_io_percent','Disk IO per task',      ['dag_id','task_id'])
etl_rows_raw    = Counter('etl_rows_raw_total',    'Raw rows inserted',     ['source'])
etl_rows_clean  = Counter('etl_rows_clean_total',  'Clean rows upserted',   ['source'])
etl_run_success = Counter('etl_run_success_total', 'Successful runs',       ['dag_id'])
etl_run_failed  = Counter('etl_run_failed_total',  'Failed runs',           ['dag_id'])

# ── Prometheus endpoint ───────────────────────────────────
Instrumentator().instrument(app).expose(app)
@app.get("/")
def root():
    return {"status": "ok", "message": "ETL Service API"}
