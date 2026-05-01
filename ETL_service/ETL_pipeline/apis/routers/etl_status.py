"""
apis/routers/etl_status.py — ETL data-readiness & manual trigger endpoints.

Endpoints
─────────
GET  /etl/status
    Returns DB connectivity + entreprise row count + whether initial_load is needed.
    Safe to call at any time — read-only.

POST /etl/trigger-initial-load
    Triggers Airflow DAG `initial_load` ONLY when entreprise table is empty.
    Supports ?force=true to override the guard (with an explicit warning).
    NEVER called automatically — strictly manual.

Environment variables consumed
──────────────────────────────
AIRFLOW_URL      — base URL of Airflow API server  (default: http://airflow-apiserver:8080)
AIRFLOW_USER     — Airflow API username             (default: admin)
AIRFLOW_PASSWORD — Airflow API password             (default: admin)
"""

import os
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query

from db.health import get_etl_readiness_status, get_entreprise_count
from db.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/etl", tags=["ETL Status"])

# ── Airflow connection settings ────────────────────────────────
_AIRFLOW_URL  = os.environ.get("AIRFLOW_URL",      "http://airflow-apiserver:8080")
_AIRFLOW_USER = os.environ.get("AIRFLOW_USER",     "airflow")
_AIRFLOW_PASS = os.environ.get("AIRFLOW_PASSWORD", "airflow")
_DAG_ID       = "initial_load"


# ─────────────────────────────────────────────────────────────
#  GET /etl/status
# ─────────────────────────────────────────────────────────────

@router.get(
    "/status",
    summary="ETL data-readiness check",
    response_description=(
        "Returns DB connectivity, entreprise row count, "
        "and whether the initial_load DAG needs to be triggered."
    ),
)
def etl_status():
    """
    Read-only health check for the ETL data layer.

    - **database_connected**: False when the DB is unreachable.
    - **entreprise_count**: Number of rows in the `entreprise` table.
    - **initial_load_required**: True when the table is empty.

    This endpoint is safe to poll at any time; it never writes to the DB.
    """
    return get_etl_readiness_status()


# ─────────────────────────────────────────────────────────────
#  POST /etl/trigger-initial-load
# ─────────────────────────────────────────────────────────────

@router.post(
    "/trigger-initial-load",
    summary="Manually trigger Airflow DAG initial_load (safe guard included)",
    response_description="Trigger result with optional warning when force=true.",
)
def trigger_initial_load(
    force: bool = Query(
        default=False,
        description=(
            "Set to true to trigger even when entreprise table already has data. "
            "This WILL re-run the full ETL and may create duplicate records "
            "if upsert logic is not perfectly idempotent."
        ),
    ),
):
    """
    Triggers the Airflow `initial_load` DAG **only when the entreprise table is empty**.

    ### Safety guard
    - If `entreprise_count > 0` and `force=false` → returns without triggering.
    - If `force=true` → triggers anyway with an explicit **warning** in the response.

    ### When to use
    Call this endpoint exactly **once** after a fresh clone + fresh Docker volumes,
    or when you intentionally want a full ETL reload.

    ### Do NOT call automatically
    This endpoint is strictly manual.  It is **not** called during container startup.
    """

    # ── 1. Check current row count ──────────────────────────
    db = SessionLocal()
    try:
        count = get_entreprise_count(db)
    except Exception as exc:
        logger.error("[TRIGGER] DB check failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Cannot reach the ETL database. Is postgres-airflow healthy?",
        )
    finally:
        db.close()

    # ── 2. Guard: refuse trigger when data exists (unless force=true) ──
    if count > 0 and not force:
        return {
            "triggered": False,
            "dag_id": _DAG_ID,
            "reason": "Entreprise table already contains data.",
            "entreprise_count": count,
            "hint": (
                "If you intentionally want a full reload, "
                "call POST /etl/trigger-initial-load?force=true — "
                "but be aware this may cause duplicate records."
            ),
        }

    # ── 3. Build Airflow API trigger payload ─────────────────
    run_id  = f"manual_api_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    payload = {
        "dag_run_id": run_id,
        "conf": {},
        "note": "Triggered via ETL FastAPI /etl/trigger-initial-load",
    }

    airflow_trigger_url = f"{_AIRFLOW_URL}/api/v2/dags/{_DAG_ID}/dagRuns"

    # ── 4. Call Airflow REST API ──────────────────────────────
    try:
        resp = httpx.post(
            airflow_trigger_url,
            json=payload,
            auth=(_AIRFLOW_USER, _AIRFLOW_PASS),
            timeout=15.0,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
    except httpx.TimeoutException:
        logger.error("[TRIGGER] Airflow API timed out at %s", airflow_trigger_url)
        raise HTTPException(
            status_code=504,
            detail=(
                f"Airflow API timed out ({airflow_trigger_url}). "
                "Is the airflow-apiserver container running?"
            ),
        )
    except httpx.HTTPStatusError as exc:
        logger.error("[TRIGGER] Airflow returned %s: %s", exc.response.status_code, exc.response.text)
        raise HTTPException(
            status_code=502,
            detail=f"Airflow API error {exc.response.status_code}: {exc.response.text}",
        )
    except httpx.RequestError as exc:
        logger.error("[TRIGGER] Cannot reach Airflow: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                f"Cannot reach Airflow at {airflow_trigger_url}. "
                "Check AIRFLOW_URL env var and container networking."
            ),
        )

    # ── 5. Success ────────────────────────────────────────────
    result = {
        "triggered": True,
        "dag_id": _DAG_ID,
        "dag_run_id": run_id,
        "airflow_ui": f"{_AIRFLOW_URL}/dags/{_DAG_ID}/runs",
        "message": (
            "initial_load DAG triggered successfully. "
            "Monitor progress at the Airflow UI link above."
        ),
    }

    if force and count > 0:
        result["warning"] = (
            f"force=true was used. The entreprise table already had {count} rows. "
            "A full ETL reload will now run — verify idempotency of your upsert logic."
        )

    logger.info("[TRIGGER] DAG %s triggered — run_id=%s | force=%s | prior_count=%d",
                _DAG_ID, run_id, force, count)
    return result
