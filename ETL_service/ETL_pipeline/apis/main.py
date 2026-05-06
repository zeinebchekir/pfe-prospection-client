import sys
sys.path.insert(0, "/app")

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge, Counter

from apis.routers import sync, entreprise, logs, notifications
from apis.routers.monitoring import router as monitoring_router
from apis.routers.rapport import router as rapport_router
from apis.routers.notifications import dispatch_notifications
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
app.include_router(sync.router,        prefix="/sync",        tags=["Sync"])
app.include_router(entreprise.router,  prefix="/entreprises", tags=["Entreprises"])
app.include_router(monitoring_router)
app.include_router(rapport_router)
app.include_router(logs.router)
app.include_router(notifications.router)

# ── Prometheus ────────────────────────────────────────────────────────────────
etl_task_cpu   = Gauge('etl_task_cpu_percent',    'CPU usage per task',  ['dag_id', 'task_id'])
etl_task_ram   = Gauge('etl_task_ram_percent',    'RAM usage per task',  ['dag_id', 'task_id'])
etl_task_disk  = Gauge('etl_task_disk_io_percent','Disk IO per task',    ['dag_id', 'task_id'])
etl_rows_raw   = Counter('etl_rows_raw_total',   'Raw rows inserted',    ['source'])
etl_rows_clean = Counter('etl_rows_clean_total', 'Clean rows upserted',  ['source'])
etl_run_ok     = Counter('etl_run_success_total','Successful runs',      ['dag_id'])
etl_run_ko     = Counter('etl_run_failed_total', 'Failed runs',          ['dag_id'])

Instrumentator().instrument(app).expose(app)


@app.get("/")
def root():
    return {"status": "ok", "message": "ETL Service API"}