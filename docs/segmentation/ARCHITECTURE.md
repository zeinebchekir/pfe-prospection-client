# Segmentation Architecture

## Scope

This document covers the end-to-end architecture from ETL ingestion to the CEO dashboard.
It focuses on the real current code paths.

## Runtime topology

```text
Frontend (Vue / Vite)           : localhost:5174
Django backend                  : localhost:8000
ETL FastAPI                     : localhost:8001
Airflow API server / UI         : localhost:8080
ETL PostgreSQL                  : postgres-airflow
Shared export volume            : /opt/airflow/exports
Segmentation export directory   : /opt/airflow/exports/segmentation
```

Important separation:

- authentication and role routing live in Django + Vue
- segmentation data lives in the ETL stack
- the segmentation page talks directly to ETL FastAPI, not to Django REST endpoints

## End-to-end data flow

```text
DataGouv / BOAMP / Sirene
    -> Airflow DAGs
    -> ETL cleaners / DB CRUD
    -> ETL PostgreSQL table `entreprise`
    -> FastAPI POST /segmentation/run
    -> market_analysis.clustering.run_clustering()
    -> decision_tree_segmentation.run_decision_tree_segmentation()
    -> JSON exports to shared volume
    -> FastAPI GET /segmentation/*
    -> frontend/src/services/segmentation.js
    -> MarketAnalysisPage.vue + market components
```

## ETL and Airflow side

The segmentation pipeline depends on ETL output, but Airflow does not execute segmentation itself.

What Airflow does:

- loads and cleans source data into `raw_leads` and then `entreprise`
- runs initial and incremental synchronization DAGs
- keeps the ETL database current

What segmentation does:

- reads the current state of `entreprise`
- performs a batch analysis on demand
- writes read-optimized JSON exports for the dashboard

### Data readiness path

Primary readiness helper:

- `GET /etl/status`

Manual initial load trigger:

- `POST /etl/trigger-initial-load`

Automatic bootstrap:

- `ETL_service/scripts/bootstrap_initial_load.py`
- Docker service `etl-bootstrap`

### Airflow DAGs relevant to segmentation input data

- `initial_load`
  - full first-time load of BOAMP and DataGouv data into `entreprise`
- `sync_datagouv`
  - incremental Sirene/DataGouv sync every 6 hours
- `sync_boamp`
  - incremental BOAMP sync daily
- `search_new_lead`
  - manual search flow
- `load_manual_lead`
  - manual lead persistence flow

The segmentation run is therefore only as current as the latest successful ETL update to `entreprise`.

## FastAPI segmentation service

Entry file:

- `ETL_service/ETL_pipeline/apis/main.py`

Route registration:

- router imported from `apis/routers/segmentation.py`
- mounted at `/segmentation`

Startup behavior:

- FastAPI calls `create_tables()` on startup
- CORS is enabled for the local Vue dev origins on ports `5173` and `5174`

### Trigger path

```text
POST /segmentation/run
    -> apis/routers/segmentation.py::run_segmentation
    -> market_analysis.clustering.run_clustering
    -> market_analysis.decision_tree_segmentation.run_decision_tree_segmentation
```

`market_analysis/clustering.py` is intentionally only a compatibility shim.
It preserves the historical function name `run_clustering(db)` so the router did not need a breaking import change.

## Export files and versioning

Default export directory:

- `SEGMENTATION_EXPORT_DIR`
- fallback: `/opt/airflow/exports/segmentation`

Files written by the current pipeline:

- `cluster_summary.json`
- `clustered_leads.json`
- `cluster_summary_YYYYMMDD_HHMM.json`
- `clustered_leads_YYYYMMDD_HHMM.json`

Files written by insight generation:

- `cluster_insights.json`
- `cluster_insights_YYYYMMDD_HHMM.json`

Files written by maturity LLM caching:

- `maturity/maturity_analysis_c{cluster}_{timestamp}.json`

Versioning behavior:

- summary and leads always write both latest and timestamped files
- insights also write latest and timestamped files
- maturity analyses are per-cluster cached files only; they are not aggregated into a separate latest index

## Error handling

### ETL dependency failures

If `entreprise` is empty:

- `POST /segmentation/run` returns `400`
- message: run the ETL pipeline first

If JSON exports do not exist yet:

- `GET /segmentation/summary`, `GET /segmentation/leads`, and `GET /segmentation/validation` return `404`

### Runtime failures inside the segmentation run

`POST /segmentation/run` handles:

- `ValueError` as `400`
- any other exception as `500`

Current implementation detail:

- the `500` response includes the Python traceback string in `detail`

That is useful for developer debugging but should be treated as a production hardening concern if the ETL API is exposed outside trusted networks.

### UI fallback behavior

- `MarketAnalysisPage.vue` treats `404` on summary as "no analysis available yet"
- other errors show a retry banner
- `LeadsExplorerTable.vue` silently falls back to empty results on fetch failure

## Environment variables

### Core ETL / database

| Variable | Used by | Purpose |
|---|---|---|
| `DATABASE_URL` | ETL FastAPI / SQLAlchemy | ETL PostgreSQL connection |
| `ETL_DATABASE_URL` | Docker compose / bootstrap | ETL PostgreSQL DSN source |
| `INSEE_TOKEN` | Airflow DAGs | Sirene incremental sync token |

### Segmentation

| Variable | Used by | Purpose |
|---|---|---|
| `SEGMENTATION_EXPORT_DIR` | segmentation router and engine | export directory override |
| `GEMINI_API_KEY` | `llm_service.py`, `digital_maturity_llm.py` | Gemini insights and maturity explanations |
| `MATURITY_LLM_CALIBRATION` | `digital_maturity_llm.py` | allow bounded `score_calibration` in LLM output |

### Airflow interaction

| Variable | Used by | Purpose |
|---|---|---|
| `AIRFLOW_URL` | ETL status / trigger endpoints | Airflow API base URL |
| `AIRFLOW_USER` | ETL status / trigger endpoints | Airflow API username |
| `AIRFLOW_PASSWORD` | ETL status / trigger endpoints | Airflow API password |
| `BOOTSTRAP_WAIT_FOR_INITIAL_LOAD` | bootstrap script | block until first DAG completes |
| `BOOTSTRAP_INITIAL_LOAD_TIMEOUT_SECONDS` | bootstrap script | polling timeout |
| `BOOTSTRAP_STALE_QUEUED_SECONDS` | bootstrap script | stale queued DAG threshold |
| `BOOTSTRAP_RESET_STALE_DAGRUNS` | bootstrap script | auto-reset stale queued runs |
| `BOOTSTRAP_MAX_TRIGGER_ATTEMPTS` | bootstrap script | bootstrap retry cap |

### Frontend

| Variable | Used by | Purpose |
|---|---|---|
| `VITE_ETL_API_URL` | `frontend/src/services/segmentation.js` | ETL FastAPI base URL |

## Production notes

- Docker maps ETL FastAPI `8001:8000`.
- The shared export volume is `shared_exports:/opt/airflow/exports`.
- Segmentation runs are read-from-DB and write-to-disk only; they do not persist segment assignments back into SQL.
- `GET /segmentation/leads` loads and filters the full `clustered_leads.json` file in memory, which is fine for current moderate volumes but not ideal for very large datasets.
- The frontend route is CEO-only, but the ETL FastAPI endpoint itself is not protected by Django auth in the current code.
- The UI only shows a compact validation badge to CEOs. Detailed validation payloads such as confusion matrices and full rule dumps should stay in developer tools and API responses, not in executive-facing components.

## File map

### Backend / ETL / FastAPI

| File | Role |
|---|---|
| `ETL_service/ETL_pipeline/apis/main.py` | ETL FastAPI entry point and router registration. |
| `ETL_service/ETL_pipeline/apis/routers/segmentation.py` | Segmentation run/read endpoints and JSON file access layer. |
| `ETL_service/ETL_pipeline/apis/routers/etl_status.py` | ETL readiness check and manual Airflow trigger endpoints. |
| `ETL_service/ETL_pipeline/db/database.py` | SQLAlchemy engine, session factory, and table creation helpers. |
| `ETL_service/ETL_pipeline/db/models.py` | ETL database schema, including the `entreprise` table consumed by segmentation. |
| `ETL_service/ETL_pipeline/db/health.py` | Read-only helpers used by ETL readiness endpoints. |
| `ETL_service/dags/dag_initial_load.py` | Airflow DAG definitions that populate and refresh ETL data. |
| `ETL_service/scripts/bootstrap_initial_load.py` | Startup guard that auto-triggers `initial_load` when `entreprise` is empty. |
| `ETL_service/Dockerfile.api` | Runtime image for ETL FastAPI. |
| `docker-compose.yml` | Service wiring, volumes, ports, and env propagation for ETL + frontend + backend. |

### Segmentation engine

| File | Role |
|---|---|
| `ETL_service/ETL_pipeline/market_analysis/clustering.py` | Backward-compatible wrapper that delegates to the decision-tree engine. |
| `ETL_service/ETL_pipeline/market_analysis/decision_tree_segmentation.py` | Main production segmentation pipeline from DB rows to JSON exports. |
| `ETL_service/ETL_pipeline/market_analysis/validation.py` | Decision-tree validation builder plus legacy KMeans validation helpers. |
| `ETL_service/ETL_pipeline/market_analysis/explainability.py` | Segment-vs-global numeric explainability layer. |
| `ETL_service/ETL_pipeline/market_analysis/llm_service.py` | Strategic insights generation and `cluster_insights.json` export. |
| `ETL_service/ETL_pipeline/market_analysis/digital_maturity.py` | Deterministic segment and lead maturity computation. |
| `ETL_service/ETL_pipeline/market_analysis/digital_maturity_baseline.py` | Sector baseline maturity scores. |
| `ETL_service/ETL_pipeline/market_analysis/digital_maturity_adjustment.py` | Rule-based maturity adjustments from internal segment aggregates. |
| `ETL_service/ETL_pipeline/market_analysis/digital_maturity_llm.py` | Gemini or fallback maturity text explanations. |
| `ETL_service/ETL_pipeline/market_analysis/text_utils.py` | Mojibake repair helpers used before export and response serving. |

### Historical but not active runtime

| File | Role |
|---|---|
| `lead_clustering.py` | Old standalone KMeans-era script kept as reference. |
| `ETL_service/ETL_pipeline/market_analysis/labeling.py` | Older v3 cluster naming helper not imported by the current pipeline. |
| `DecisionTree_Restructured.ipynb` | Notebook reference for decision-tree work, not production runtime. |

### Frontend

Frontend file details are documented in [FRONTEND.md](FRONTEND.md), but the primary entry points are:

- `frontend/src/services/segmentation.js`
- `frontend/src/pages/manager/MarketAnalysisPage.vue`
- `frontend/src/components/market/*`
- `frontend/src/router/index.js`
- `frontend/src/components/AppSidebar.vue`
