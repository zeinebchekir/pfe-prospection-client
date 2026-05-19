"""
apis/routers/generate_leads.py — Incremental lead generation endpoint.

Endpoints
─────────
POST /etl/generate-new-leads
    Triggers the Airflow `generate_new_leads` DAG.
    Accepts an optional `pages_per_batch` parameter.
    Returns run_id and monitoring link.

GET  /etl/generate-new-leads/checkpoints
    Returns the current checkpoint state for all NAF groups.
    Useful for monitoring how far the incremental pagination has progressed.

POST /etl/generate-new-leads/reset-checkpoints
    Resets ALL checkpoints back to page 0.
    Use when you want the next button click to restart from page 1.

Environment variables consumed
──────────────────────────────
AIRFLOW_URL      — base URL of Airflow API server (default: http://airflow-apiserver:8080)
AIRFLOW_USER     — Airflow API username             (default: airflow)
AIRFLOW_PASSWORD — Airflow API password             (default: airflow)
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from db.database import SessionLocal
from db.checkpoint_crud import get_all_checkpoints, reset_all_checkpoints

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/etl", tags=["ETL — Generate Leads"])

# ── Airflow connection settings ────────────────────────────────
_AIRFLOW_URL  = os.environ.get("AIRFLOW_URL",      "http://airflow-apiserver:8080")
_AIRFLOW_USER = os.environ.get("AIRFLOW_USER",     "airflow")
_AIRFLOW_PASS = os.environ.get("AIRFLOW_PASSWORD", "airflow")
_DAG_ID       = "generate_new_leads"


# ─────────────────────────────────────────────────────────────
#  Schemas
# ─────────────────────────────────────────────────────────────

class GenerateLeadsRequest(BaseModel):
    pages_per_batch: int = 5


# ─────────────────────────────────────────────────────────────
#  Airflow 3 JWT Authentication
# ─────────────────────────────────────────────────────────────

def _get_airflow_token() -> str:
    """
    Obtains a short-lived JWT token from Airflow 3's auth endpoint.

    Airflow 3 removed HTTP Basic Auth on the REST API.
    The correct flow is:
      POST /auth/token  { username, password }  → { access_token }
      Then: Authorization: Bearer <access_token>

    Raises HTTPException(502) if the token cannot be obtained.
    """
    url = f"{_AIRFLOW_URL}/auth/token"
    try:
        resp = httpx.post(
            url,
            json={"username": _AIRFLOW_USER, "password": _AIRFLOW_PASS},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=10.0,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise HTTPException(
                status_code=502,
                detail=f"Airflow /auth/token returned no access_token: {resp.text[:200]}",
            )
        logger.debug("[GENERATE-LEADS] Got Airflow JWT token ✅")
        return token

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Airflow /auth/token timed out.")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Airflow /auth/token error {exc.response.status_code}: {exc.response.text[:200]}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot reach Airflow at {url}: {exc}",
        )


def _bearer_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _trigger_dag_via_cli(dag_id: str, conf: dict) -> dict:
    """
    Fallback for environments where Airflow 3 exposes DAG reads over REST
    but rejects POST /dagRuns with a false 404.
    """
    run_id = f"generate_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    logical_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conf_json = json.dumps(conf, separators=(",", ":"))

    try:
        subprocess.run(
            ["airflow", "dags", "unpause", dag_id],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

        result = subprocess.run(
            [
                "airflow",
                "dags",
                "trigger",
                dag_id,
                "--run-id",
                run_id,
                "--logical-date",
                logical_date,
                "--conf",
                conf_json,
            ],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Airflow CLI is not installed in the ETL API container. "
                "Rebuild the etl-fastapi service after updating Dockerfile.api."
            ),
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Airflow CLI trigger timed out while launching the DAG.",
        )

    combined_output = "\n".join(
        part for part in [result.stdout.strip(), result.stderr.strip()] if part
    )

    if result.returncode != 0 and "already exists" not in combined_output.lower():
        logger.error("[GENERATE-LEADS] Airflow CLI trigger failed: %s", combined_output)
        raise HTTPException(
            status_code=502,
            detail=f"Airflow CLI trigger failed: {combined_output[:400]}",
        )

    logger.info("[GENERATE-LEADS] DAG %s triggered via CLI fallback ✅", dag_id)
    return {
        "run_id": run_id,
        "airflow_response": {
            "triggered_via": "airflow_cli_fallback",
            "output": combined_output[:400],
        },
    }


# ─────────────────────────────────────────────────────────────
#  Helper: unpause DAG
# ─────────────────────────────────────────────────────────────

def _unpause_dag(dag_id: str, token: str) -> None:
    """
    Sends PATCH /api/v2/dags/{dag_id} with is_paused=false.
    Silently ignores non-fatal errors.
    Required because AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true.
    """
    url = f"{_AIRFLOW_URL}/api/v2/dags/{dag_id}"
    try:
        resp = httpx.patch(
            url,
            json={"is_paused": False},
            headers=_bearer_headers(token),
            timeout=10.0,
        )
        if resp.status_code in (200, 204):
            logger.info("[GENERATE-LEADS] DAG %s unpaused ✅", dag_id)
        else:
            logger.warning(
                "[GENERATE-LEADS] Unpause returned %d: %s (non-fatal)",
                resp.status_code, resp.text[:200],
            )
    except Exception as exc:
        logger.warning("[GENERATE-LEADS] Unpause call failed (non-fatal): %s", exc)


# ─────────────────────────────────────────────────────────────
#  Helper: trigger Airflow DAG
# ─────────────────────────────────────────────────────────────

def _trigger_dag(dag_id: str, conf: dict) -> dict:
    """
    1. Gets a JWT token (Airflow 3 auth)
    2. Unpauses the DAG   (PATCH /api/v2/dags/{dag_id})
    3. Triggers a new run (POST  /api/v2/dags/{dag_id}/dagRuns)
    """
    # Step 1 — get a JWT token
    token = _get_airflow_token()

    # Step 2 — unpause first (idempotent)
    _unpause_dag(dag_id, token)

    # Step 3 — trigger
    run_id  = f"generate_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    logical_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "dag_run_id":    run_id,
        "logical_date":  logical_date,
        "conf":          conf,
        "note":          "Triggered via ETL FastAPI /etl/generate-new-leads",
    }
    url = f"{_AIRFLOW_URL}/api/v2/dags/{dag_id}/dagRuns"

    try:
        resp = httpx.post(
            url,
            json=payload,
            headers=_bearer_headers(token),
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"run_id": run_id, "airflow_response": resp.json()}

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Airflow API timed out ({url}). Is airflow-apiserver running?",
        )
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:400]
        if exc.response.status_code == 404 and "DAG with dag_id" in body:
            logger.warning(
                "[GENERATE-LEADS] Airflow REST trigger returned a false 404 for %s. "
                "Falling back to local Airflow CLI.",
                dag_id,
            )
            return _trigger_dag_via_cli(dag_id, conf)
        logger.error(
            "[GENERATE-LEADS] Airflow returned %s: %s",
            exc.response.status_code, body,
        )
        raise HTTPException(
            status_code=502,
            detail=f"Airflow API error {exc.response.status_code}: {body}",
        )
    except httpx.RequestError as exc:
        logger.error("[GENERATE-LEADS] Cannot reach Airflow: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Cannot reach Airflow at {url}. Check AIRFLOW_URL and container networking.",
        )


# ─────────────────────────────────────────────────────────────
#  POST /etl/generate-new-leads
# ─────────────────────────────────────────────────────────────

@router.post(
    "/generate-new-leads",
    summary="Trigger incremental DataGouv lead generation (commercial button)",
    response_description="Trigger result with run_id and monitoring links.",
)
def generate_new_leads(body: GenerateLeadsRequest = GenerateLeadsRequest()):
    """
    Triggers the `generate_new_leads` Airflow DAG.

    ### What this does
    - Reads checkpoints for every NAF group.
    - Fetches the **next** `pages_per_batch` pages (never restarts from page 1).
    - Applies NAF filter → extraction → completeness filter → **PME exclusion**.
    - Upserts clean records into the `entreprise` table.
    - Advances checkpoints only after a successful batch.

    ### Config options
    - **pages_per_batch** (default 5): number of DataGouv API pages fetched per
      NAF group per run.  Each page contains 25 companies, so 5 pages = 125 raw
      records per group before filtering.

    ### Safe to call multiple times
    Each call fetches the *next* pages.  Calling it twice quickly will start two
    overlapping runs — Airflow's task concurrency handles this gracefully because
    checkpoints are committed only after success.
    """
    pages_per_batch = max(1, min(body.pages_per_batch, 50))  # clamp 1–50

    conf = {
        "pages_per_batch": pages_per_batch,
        "triggered_by": "commercial_button",
    }

    result = _trigger_dag(_DAG_ID, conf)
    run_id = result["run_id"]

    logger.info(
        "[GENERATE-LEADS] DAG %s triggered — run_id=%s | pages_per_batch=%d",
        _DAG_ID, run_id, pages_per_batch,
    )

    return {
        "status":          "triggered",
        "dag_id":          _DAG_ID,
        "run_id":          run_id,
        "pages_per_batch": pages_per_batch,
        "airflow_ui":      f"{_AIRFLOW_URL}/dags/{_DAG_ID}/runs",
        "message": (
            f"generate_new_leads DAG triggered successfully. "
            f"Each NAF group will fetch {pages_per_batch} page(s) × 25 = "
            f"{pages_per_batch * 25} raw records before filtering. "
            f"Monitor progress at the Airflow UI link above."
        ),
    }


# ─────────────────────────────────────────────────────────────
#  GET /etl/generate-new-leads/checkpoints
# ─────────────────────────────────────────────────────────────

@router.get(
    "/generate-new-leads/checkpoints",
    summary="View current pagination checkpoints for all NAF groups",
)
def get_checkpoints():
    """
    Returns the current checkpoint state for every NAF group.

    Use this to understand how far the incremental pagination has progressed
    and when a NAF group has been fully exhausted (last_page_fetched >= total_pages).
    """
    db = SessionLocal()
    try:
        rows = get_all_checkpoints(db, source="datagouv")
        return {
            "count": len(rows),
            "checkpoints": [
                {
                    "filter_key":        r.filter_key,
                    "naf_codes":         r.naf_codes,
                    "last_page_fetched": r.last_page_fetched,
                    "total_pages":       r.total_pages,
                    "total_results":     r.total_results,
                    "total_fetched":     r.total_fetched,
                    "total_inserted":    r.total_inserted,
                    "per_page":          r.per_page,
                    "last_run_id":       r.last_run_id,
                    "updated_at":        r.updated_at.isoformat() if r.updated_at else None,
                    "exhausted":         (
                        r.total_pages is not None and
                        r.last_page_fetched >= r.total_pages
                    ),
                }
                for r in rows
            ],
        }
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
#  POST /etl/generate-new-leads/reset-checkpoints
# ─────────────────────────────────────────────────────────────

@router.post(
    "/generate-new-leads/reset-checkpoints",
    summary="Reset all NAF group checkpoints back to page 0",
)
def reset_checkpoints_endpoint():
    """
    Resets ALL checkpoints for the `datagouv` source back to page 0.

    After calling this endpoint, the next click of the \"Générer nouveaux leads\"
    button will restart from page 1 for every NAF group.

    **Warning:** This does NOT delete any companies already in the database.
    It only resets the pagination progress counter.
    """
    db = SessionLocal()
    try:
        count = reset_all_checkpoints(db, source="datagouv")
        logger.info("[GENERATE-LEADS] Reset %d checkpoints.", count)
        return {
            "status":  "reset",
            "message": f"{count} checkpoint(s) reset to page 0. Next run will start from page 1.",
            "count":   count,
        }
    finally:
        db.close()
