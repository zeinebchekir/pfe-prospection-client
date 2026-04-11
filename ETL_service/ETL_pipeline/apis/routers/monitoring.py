import glob
import json
import time
import asyncio
import os
from datetime import datetime
from fastapi import APIRouter, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from db.database import SessionLocal

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _serialize(obj):
    """Convertit les dates en string pour JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _get_pipeline_state(dag_id: str) -> dict:
    """
    Lit dag_run + task_instance depuis PostgreSQL Airflow.
    Retourne l'état complet du dernier run.
    """
    db = SessionLocal()
    try:
        run = db.execute(text("""
            SELECT
                run_id,
                state,
                start_date,
                end_date,
                execution_date,
                conf
            FROM dag_run
            WHERE dag_id = :dag_id
            ORDER BY execution_date DESC
            LIMIT 1
        """), {"dag_id": dag_id}).mappings().first()

        if not run:
            return {"run": None, "tasks": [], "metrics": {}}

        run_dict = dict(run)

        tasks = db.execute(text("""
            SELECT
                task_id,
                state,
                start_date,
                end_date,
                duration,
                try_number,
                hostname,
                queued_dttm
            FROM task_instance
            WHERE dag_id    = :dag_id
              AND run_id    = :run_id
            ORDER BY start_date ASC NULLS LAST
        """), {
            "dag_id": dag_id,
            "run_id": run_dict["run_id"]
        }).mappings().all()

        tasks_list = [dict(t) for t in tasks]

        # Calcul du progress
        total = len(tasks_list)
        done  = sum(
            1 for t in tasks_list
            if t["state"] in ("success", "failed", "skipped", "upstream_failed")
        )
        progress = round((done / total * 100)) if total > 0 else 0

        # Métriques ETL depuis tes tables
        metrics = {}
        try:
            raw_metrics = db.execute(text("""
                SELECT
                    source,
                    COUNT(*)                    AS total,
                    ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy,
                    MAX(loaded_at)              AS last_loaded
                FROM raw_leads
                WHERE dag_run_id = :run_id
                GROUP BY source
            """), {"run_id": run_dict["run_id"]}).mappings().all()

            clean_metrics = db.execute(text("""
                SELECT
                    COUNT(*)                    AS total,
                    ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy,
                    MAX(updated_at)             AS last_updated
                FROM entreprise
                WHERE dag_run_id = :run_id
            """), {"run_id": run_dict["run_id"]}).mappings().first()

            metrics = {
                "raw":   [dict(r) for r in raw_metrics],
                "clean": dict(clean_metrics) if clean_metrics else {},
            }
        except Exception:
            pass

        return {
            "run":      run_dict,
            "tasks":    tasks_list,
            "progress": progress,
            "metrics":  metrics,
        }

    finally:
        db.close()


def _read_log_file(dag_id: str, run_id: str, task_id: str) -> str | None:
    """Retourne le chemin du dernier fichier log d'une task."""
    pattern = (
        f"/opt/airflow/logs/dag_id={dag_id}"
        f"/run_id={run_id}"
        f"/task_id={task_id}"
        f"/attempt=*.log"
    )
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def _parse_log_line(line: str) -> dict:
    """Parse une ligne de log et détecte son niveau."""
    line = line.strip()
    lvl  = "info"
    if "ERROR"   in line: lvl = "err"
    elif "WARNING" in line: lvl = "warn"
    elif any(x in line.lower() for x in [
        "success", "inserted", "upserted",
        "lignes", "rows", "ok"
    ]): lvl = "ok"
    return {"text": line, "lvl": lvl}


# ─────────────────────────────────────────────
#  ENDPOINT 1 — État du pipeline (polling 2s)
# ─────────────────────────────────────────────

@router.get("/state/{dag_id}")
def get_pipeline_state(dag_id: str):
    """
    Vue appelle cet endpoint toutes les 2s.
    Retourne l'état complet du dernier run + toutes les tasks.
    """
    state = _get_pipeline_state(dag_id)
    return json.loads(json.dumps(state, default=_serialize))


# ─────────────────────────────────────────────
#  ENDPOINT 2 — Historique des runs
# ─────────────────────────────────────────────

@router.get("/history/{dag_id}")
def get_history(dag_id: str, limit: int = 10):
    """Derniers N runs d'un DAG."""
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                run_id,
                state,
                execution_date,
                start_date,
                end_date,
                EXTRACT(EPOCH FROM (end_date - start_date)) AS duration_sec
            FROM dag_run
            WHERE dag_id = :dag_id
            ORDER BY execution_date DESC
            LIMIT :limit
        """), {"dag_id": dag_id, "limit": limit}).mappings().all()
        return json.loads(json.dumps([dict(r) for r in rows], default=_serialize))
    finally:
        db.close()


# ─────────────────────────────────────────────
#  ENDPOINT 3 — Logs d'une task (snapshot)
# ─────────────────────────────────────────────

@router.get("/logs/{dag_id}/{run_id}/{task_id}")
def get_task_logs(dag_id: str, run_id: str, task_id: str):
    """Retourne les 300 dernières lignes de log d'une task."""
    filepath = _read_log_file(dag_id, run_id, task_id)
    if not filepath:
        return {"lines": [], "error": "Log file not found"}

    lines = []
    with open(filepath, "r", errors="replace") as f:
        for line in f.readlines()[-300:]:
            if line.strip():
                lines.append(_parse_log_line(line))
    return {"lines": lines}


# ─────────────────────────────────────────────
#  ENDPOINT 4 — Stream logs (tail -f)
# ─────────────────────────────────────────────

@router.get("/logs/{dag_id}/{run_id}/{task_id}/stream")
def stream_task_logs(dag_id: str, run_id: str, task_id: str):
    """
    Stream HTTP du fichier log — comportement identique à tail -f.
    Vue lit ce stream avec fetch() + ReadableStream.
    S'arrête automatiquement quand la task est terminée.
    """
    filepath = _read_log_file(dag_id, run_id, task_id)

    if not filepath:
        def empty():
            yield "Log file not found\n"
        return StreamingResponse(empty(), media_type="text/plain")

    def generate():
        db = SessionLocal()
        try:
            with open(filepath, "r", errors="replace") as f:
                # 1. Envoyer tout ce qui existe déjà
                for line in f:
                    if line.strip():
                        yield json.dumps(_parse_log_line(line)) + "\n"

                # 2. Continuer en tail -f tant que la task tourne
                while True:
                    line = f.readline()
                    if line:
                        if line.strip():
                            yield json.dumps(_parse_log_line(line)) + "\n"
                    else:
                        # Vérifier si la task est terminée
                        task = db.execute(text("""
                            SELECT state FROM task_instance
                            WHERE dag_id  = :dag_id
                              AND run_id  = :run_id
                              AND task_id = :task_id
                        """), {
                            "dag_id":  dag_id,
                            "run_id":  run_id,
                            "task_id": task_id,
                        }).scalar()

                        if task in ("success", "failed", "skipped", "upstream_failed"):
                            break  # Task terminée → fin du stream

                        time.sleep(0.5)
        finally:
            db.close()

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


# ─────────────────────────────────────────────
#  ENDPOINT 5 — Métriques globales ETL
# ─────────────────────────────────────────────

@router.get("/metrics")
def get_metrics():
    """Métriques globales raw_leads + entreprise."""
    db = SessionLocal()
    try:
        raw = db.execute(text("""
            SELECT
                source,
                COUNT(*)                            AS total,
                ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy,
                MAX(loaded_at)                      AS last_loaded
            FROM raw_leads
            GROUP BY source
        """)).mappings().all()

        clean = db.execute(text("""
            SELECT
                COUNT(*)                            AS total,
                ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy,
                MAX(updated_at)                     AS last_updated
            FROM entreprise
        """)).mappings().first()

        scheduler = db.execute(text("""
            SELECT latest_heartbeat
            FROM job
            WHERE job_type = 'SchedulerJob'
            ORDER BY latest_heartbeat DESC
            LIMIT 1
        """)).scalar()

        return json.loads(json.dumps({
            "raw":       [dict(r) for r in raw],
            "clean":     dict(clean) if clean else {},
            "scheduler": {"last_heartbeat": scheduler},
        }, default=_serialize))

    finally:
        db.close()


# ─────────────────────────────────────────────
#  ENDPOINT 6 — Déclencher un DAG
# ─────────────────────────────────────────────

@router.post("/trigger/{dag_id}")
def trigger_dag(dag_id: str, conf: dict = {}):
    import requests
    url  = os.getenv("AIRFLOW_URL",      "http://airflow-apiserver:8080")
    user = os.getenv("AIRFLOW_USER",     "ali")
    pwd  = os.getenv("AIRFLOW_PASSWORD", "ali")

    try:
        resp = requests.post(
            f"{url}/api/v2/dags/{dag_id}/dagRuns",
            json={"conf": conf},
            auth=(user, pwd),
            timeout=10,
        )
        return {"status": resp.status_code, "data": resp.json()}
    except requests.RequestException as e:
        return {"status": 500, "error": str(e)}