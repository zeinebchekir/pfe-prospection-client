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

import httpx
import psutil
from datetime import datetime

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

import decimal

def _serialize(obj):
    """Convertit les dates en string pour JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return float(obj)
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
                logical_date,
                conf
            FROM dag_run
            WHERE dag_id = :dag_id
            ORDER BY logical_date DESC
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
            # raw_metrics = db.execute(text("""
            #     SELECT
            #         source,
            #         COUNT(*)                    AS total,
            #         ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy,
            #         MAX(loaded_at)              AS last_loaded
            #     FROM entreprise
            #     WHERE dag_run_id = :run_id
            #     GROUP BY source
            # """), {"run_id": run_dict["run_id"]}).mappings().all()

            clean_metrics = db.execute(text("""
                SELECT
                    COUNT(*)                    AS total,
                    ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy,
                    MAX(updated_at)             AS last_updated
                FROM entreprise
                WHERE dag_run_id = :run_id
            """), {"run_id": run_dict["run_id"]}).mappings().first()

            metrics = {
                # "raw":   [dict(r) for r in raw_metrics],
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
                logical_date,
                start_date,
                end_date,
                EXTRACT(EPOCH FROM (end_date - start_date)) AS duration_sec
            FROM dag_run
            WHERE dag_id = :dag_id
            ORDER BY logical_date DESC
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
@router.get("/metrics/{dag_id}/{run_id}")
def get_run_metrics(dag_id: str, run_id: str):
    """Retourne les métriques XCom de chaque task pour un run donné."""
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT task_id, key, value
            FROM xcom
            WHERE dag_id = :dag_id
              AND run_id = :run_id
              AND key IN (
                'total_raw', 'total_extracted',
                'total_raw_loaded', 'total_clean',
                'total_clean_loaded', 'watermark_start'
              )
        """), {"dag_id": dag_id, "run_id": run_id}).fetchall()

        # Regrouper par task_id
        metrics = {}
        for task_id, key, value in rows:
            if task_id not in metrics:
                metrics[task_id] = {}
            # La valeur XCom est stockée en JSON dans Airflow
            try:
                metrics[task_id][key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                metrics[task_id][key] = value

        return {"dag_id": dag_id, "run_id": run_id, "metrics": metrics}
    finally:
        db.close()


@router.get("/metrics")
def get_metrics():
    db = SessionLocal()
    try:
        today = datetime.now().strftime("%Y-%m-%d")

        # raw = db.execute(text("""
        #     SELECT
        #         source,
        #         COUNT(*)                                AS total,
        #         ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy,
        #         MAX(loaded_at)                          AS last_loaded
        #     FROM raw_leads
        #     GROUP BY source
        # """)).mappings().all()

        clean = db.execute(text("""
            SELECT
                COUNT(*)                                AS total,
                ROUND(AVG(taux_completude)::numeric, 2) AS completude_moy,
                MAX(updated_at)                         AS last_updated
            FROM entreprise
        """)).mappings().first()

        # Lignes insérées aujourd'hui
        inserted_today = db.execute(text("""
            SELECT COUNT(*) FROM entreprise
            WHERE DATE(created_at) = :today
        """), {"today": today}).scalar() or 0

        # Lignes modifiées aujourd'hui (updated mais pas créées aujourd'hui)
        updated_today = db.execute(text("""
            SELECT COUNT(*) FROM entreprise
            WHERE DATE(updated_at) = :today
              AND DATE(created_at) != :today
        """), {"today": today}).scalar() or 0

        scheduler = db.execute(text("""
            SELECT latest_heartbeat FROM job
            WHERE job_type = 'SchedulerJob'
            ORDER BY latest_heartbeat DESC
            LIMIT 1
        """)).scalar()

        return json.loads(json.dumps({
            # "raw":            [dict(r) for r in raw],
            "clean":          dict(clean) if clean else {},
            "inserted_today": inserted_today,
            "updated_today":  updated_today,
            "scheduler":      {"last_heartbeat": scheduler},
        }, default=_serialize))

    finally:
        db.close()

# ─────────────────────────────────────────────
#  ENDPOINT 6 — Déclencher un DAG
# ─────────────────────────────────────────────

def _get_airflow_token(base_url: str, user: str, pwd: str) -> str:
    """
    Airflow 3 n'accepte plus Basic Auth sur /api/v2.
    Il faut d'abord obtenir un JWT via /auth/token.
    """
    import requests
    resp = requests.post(
        f"{base_url}/auth/token",
        json={"username": user, "password": pwd},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@router.post("/trigger/{dag_id}")
def trigger_dag(dag_id: str, conf: dict = {}):
    import requests

    url  = os.getenv("AIRFLOW_URL",      "http://airflow-apiserver:8080")
    user = os.getenv("AIRFLOW_USER",     "ali")
    pwd  = os.getenv("AIRFLOW_PASSWORD", "ali")

    try:
        # 1. Obtenir le token JWT Airflow 3
        token = _get_airflow_token(url, user, pwd)

        # 2. Déclencher le DAG avec le token
        # Airflow 3 exige logical_date dans le body
        from datetime import timezone
        payload = {
            "conf":         conf if conf else {},
            "logical_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        }
        resp = requests.post(
            f"{url}/api/v2/dags/{dag_id}/dagRuns",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return {"status": resp.status_code, "data": resp.json()}

    except requests.RequestException as e:
        return {"status": 500, "error": str(e)}
@router.get("/runs/today/{dag_id}")



#compter les runs depuis l'API Airflow.
def get_today_runs(dag_id: str):
    db = SessionLocal()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        rows = db.execute(text("""
            SELECT state, COUNT(*) as cnt
            FROM dag_run
            WHERE dag_id  = :dag_id
              AND DATE(logical_date) = :today
            GROUP BY state
        """), {"dag_id": dag_id, "today": today}).fetchall()

        counts = {"success": 0, "failed": 0, "running": 0, "total": 0}
        for state, cnt in rows:
            counts[state] = cnt
            counts["total"] += cnt

        return counts
    finally:
        db.close()






async def _query_prometheus(query: str) -> float | None:
    """Exécute une PromQL query et retourne la valeur scalaire."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": query}
            )
            data = resp.json()
            results = data.get("data", {}).get("result", [])
            if results:
                return float(results[0]["value"][1])
    except Exception:
        pass
    return None


async def _query_prometheus_range(
    query: str,
    start: str,
    end: str,
    step: str = "15s"
) -> list:
    """Exécute une PromQL range query — retourne une liste de [timestamp, value]."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query_range",
                params={"query": query, "start": start, "end": end, "step": step}
            )
            data = resp.json()
            results = data.get("data", {}).get("result", [])
            if results:
                return results[0].get("values", [])
    except Exception:
        pass
    return []


# ── Endpoint : ressources système globales ──────────────
@router.get("/resources/system")
async def get_system_resources():
    """CPU / RAM / Disk en temps réel via Node Exporter + Prometheus."""

    cpu_query  = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
    ram_query  = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
    disk_query = '100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)'

    cpu, ram, disk = await asyncio.gather(
        _query_prometheus(cpu_query),
        _query_prometheus(ram_query),
        _query_prometheus(disk_query),
    )

    # Fallback psutil si Prometheus pas encore disponible
    if cpu is None:
        cpu  = psutil.cpu_percent(interval=0.1)
        ram  = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent

    return {
        "cpu":  round(cpu  or 0, 1),
        "ram":  round(ram  or 0, 1),
        "disk": round(disk or 0, 1),
        "source": "prometheus" if cpu is not None else "psutil",
    }


# ── Endpoint : ressources par task (pendant l'exécution) ─
@router.get("/resources/task/{dag_id}/{run_id}/{task_id}")
async def get_task_resources(dag_id: str, run_id: str, task_id: str):
    """
    Ressources consommées pendant l'exécution d'une task spécifique.
    Récupère les métriques dans la fenêtre temporelle start_date → end_date.
    """
    db = SessionLocal()
    try:
        task = db.execute(text("""
            SELECT start_date, end_date, state
            FROM task_instance
            WHERE dag_id  = :dag_id
              AND run_id  = :run_id
              AND task_id = :task_id
        """), {"dag_id": dag_id, "run_id": run_id, "task_id": task_id}).mappings().first()

        if not task or not task["start_date"]:
            return {"cpu": 0, "ram": 0, "disk": 0}

        start = task["start_date"].isoformat()
        end   = (task["end_date"] or datetime.utcnow()).isoformat()

        cpu_query  = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[30s])) * 100)'
        ram_query  = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        disk_query = 'rate(node_disk_io_time_seconds_total[30s]) * 100'

        cpu_vals, ram_vals, disk_vals = await asyncio.gather(
            _query_prometheus_range(cpu_query,  start, end, "15s"),
            _query_prometheus_range(ram_query,  start, end, "15s"),
            _query_prometheus_range(disk_query, start, end, "15s"),
        )

        def avg_values(vals):
            if not vals: return 0
            return round(sum(float(v[1]) for v in vals) / len(vals), 1)

        return {
            "cpu":       avg_values(cpu_vals),
            "ram":       avg_values(ram_vals),
            "disk":      avg_values(disk_vals),
            "cpu_series": [[v[0], round(float(v[1]), 1)] for v in cpu_vals],
            "ram_series": [[v[0], round(float(v[1]), 1)] for v in ram_vals],
        }

    finally:
        db.close()


# ── Endpoint : historique CPU sur N minutes ──────────────
@router.get("/resources/history")
async def get_resources_history(minutes: int = 10):
    """Série temporelle CPU/RAM sur les N dernières minutes."""
    end   = datetime.utcnow().isoformat() + "Z"
    start = datetime.utcnow().replace(
        minute=datetime.utcnow().minute - minutes
    ).isoformat() + "Z"

    cpu_query = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
    ram_query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'

    cpu_series, ram_series = await asyncio.gather(
        _query_prometheus_range(cpu_query, start, end, "30s"),
        _query_prometheus_range(ram_query, start, end, "30s"),
    )

    return {
        "cpu": [[v[0], round(float(v[1]), 1)] for v in cpu_series],
        "ram": [[v[0], round(float(v[1]), 1)] for v in ram_series],
    }        






    ############## superviser les ressources depuis xcom  ##############


    @router.get("/resources/task/{dag_id}/{run_id}/{task_id}")
    def get_task_resources(dag_id: str, run_id: str, task_id: str):
        db = SessionLocal()
        try:
            # Lire les XCom poussés par le décorateur
            xcoms = db.execute(text("""
                SELECT key, value
            FROM xcom
            WHERE dag_id  = :dag_id
              AND run_id  = :run_id
              AND task_id = :task_id
              AND key IN ('cpu_used', 'ram_used_mb', 'ram_delta_mb')
            """), {
            "dag_id":  dag_id,
            "run_id":  run_id,
            "task_id": task_id,
            }).mappings().all()

            xcom_map = {x["key"]: x["value"] for x in xcoms}

            cpu      = float(xcom_map.get("cpu_used",    0) or 0)
            ram_mb   = float(xcom_map.get("ram_used_mb", 0) or 0)
            ram_pct  = round((ram_mb / 4096) * 100, 1)  # 4GB total

        # Fallback estimation si XCom pas encore disponible
            if cpu == 0 and ram_pct == 0:
                cpu, ram_pct, disk = _estimate_task_resources(task_id, 0)
            else:
                disk = _estimate_task_resources(task_id, 0)[2]

            return {
                "cpu":       cpu,
                "ram":       ram_pct,
                "ram_mb":    ram_mb,
                "disk":      disk,
                "source":    "xcom" if xcom_map else "estimated",
            }
        finally:
            db.close()



######################### ANALYTICS ######################""""  


from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from db.database import get_db

# WARNING: Make sure these imports match your actual paths. 
# Previously this file used db.database.SessionLocal
from .schemas.monitoringSchema import (
    DagSuccessRateItem, TaskDurationItem,
    VolumeItem, DataQualityItem, KPISummary
)


@router.get("/dag-success-rate", response_model=List[DagSuccessRateItem])
def get_dag_success_rate(days: int = 14, db: Session = Depends(get_db)):
    """Graph 1 — taux succès/échec/retry par DAG"""
    query = text("""
        SELECT
            dag_id,
            COUNT(*) FILTER (WHERE state = 'success') AS success,
            COUNT(*) FILTER (WHERE state = 'failed')  AS failed,
            COUNT(*) FILTER (WHERE state = 'up_for_retry') AS up_for_retry,
            COUNT(*) AS total
        FROM dag_run
        WHERE logical_date >= NOW() - CAST(:days || ' days' AS INTERVAL)
        GROUP BY dag_id
        ORDER BY dag_id
    """)
    rows = db.execute(query, {"days": days}).fetchall()
    result = []
    for row in rows:
        total = row.total or 1
        result.append(DagSuccessRateItem(
            dag_id=row.dag_id,
            success=row.success,
            failed=row.failed,
            up_for_retry=row.up_for_retry,
            total=total,
            success_rate=round(row.success / total * 100, 1)
        ))
    return result


@router.get("/task-duration", response_model=List[TaskDurationItem])
def get_task_duration(dag_id: str = "sync_boamp", days: int = 7,
                      db: Session = Depends(get_db)):
    """Graph 2 — durée moyenne par tâche (pour un DAG donné)"""
    query = text("""
        SELECT
            task_id,
            ROUND(AVG(EXTRACT(EPOCH FROM (end_date - start_date))), 1) AS avg_duration_sec,
            ROUND(MAX(EXTRACT(EPOCH FROM (end_date - start_date))), 1) AS max_duration_sec
        FROM task_instance
        WHERE dag_id = :dag_id
          AND start_date >= NOW() - CAST(:days || ' days' AS INTERVAL)
          AND state = 'success'
          AND end_date IS NOT NULL
        GROUP BY task_id
        ORDER BY avg_duration_sec DESC
    """)
    rows = db.execute(query, {"dag_id": dag_id, "days": days}).fetchall()
    return [TaskDurationItem(
        task_id=row.task_id,
        avg_duration_sec=float(row.avg_duration_sec or 0),
        max_duration_sec=float(row.max_duration_sec or 0)
    ) for row in rows]


@router.get("/volume-over-time", response_model=List[VolumeItem])
def get_volume_over_time(days: int = 7, db: Session = Depends(get_db)):
    """Graph 3 — volume traité par source/jour (via XCom)"""
    
    query = text("""
        SELECT
            DATE(ti.start_date)::text AS date,
            ti.dag_id,
            ti.task_id,
            COALESCE(
                (xc.value::jsonb #>> '{}')::int, 0
            ) AS records_processed
        FROM task_instance ti
        LEFT JOIN xcom xc
            ON xc.dag_id = ti.dag_id
           AND xc.task_id = ti.task_id
           AND xc.run_id = ti.run_id
           AND xc.key = 'total_clean_loaded'
        WHERE ti.task_id IN ('load_clean_boamp', 'load_clean_sirene')
          AND ti.start_date >= NOW() - CAST(:days || ' days' AS INTERVAL)
          AND ti.state = 'success'
        ORDER BY date, ti.dag_id
    """)
    
    # Exécution de la requête en passant le paramètre dynamique 'days'
    rows = db.execute(query, {"days": days}).fetchall()
    
    # On retourne la liste en n'oubliant pas d'inclure le task_id
    return [VolumeItem(
        date=row.date,
        dag_id=row.dag_id,
        task_id=row.task_id,  # <-- Ajouté ici
        records_processed=row.records_processed
    ) for row in rows]


@router.get("/data-quality", response_model=List[DataQualityItem])
def get_data_quality(db: Session = Depends(get_db)):
    """Graph 4 — taux de remplissage des champs critiques sur la table entreprise"""
    query = text("""
        SELECT
            'siret' AS field_name,
            ROUND(100.0 * COUNT(*) FILTER (WHERE siret IS NOT NULL AND siret != '')
                / NULLIF(COUNT(*), 0), 1) AS fill_rate
        FROM entreprise
        WHERE created_at >= NOW() - INTERVAL '7 days'

        UNION ALL SELECT 'nom',
            ROUND(100.0 * COUNT(*) FILTER (WHERE nom IS NOT NULL AND nom != '')
                / NULLIF(COUNT(*), 0), 1)
        FROM entreprise WHERE created_at >= NOW() - INTERVAL '7 days'
        
        UNION ALL SELECT 'ville',
            ROUND(100.0 * COUNT(*) FILTER (WHERE ville IS NOT NULL AND ville != '')
                / NULLIF(COUNT(*), 0), 1)
        FROM entreprise WHERE created_at >= NOW() - INTERVAL '7 days'

        UNION ALL SELECT 'telephone',
            ROUND(100.0 * COUNT(*) FILTER (WHERE telephone IS NOT NULL AND telephone != '')
                / NULLIF(COUNT(*), 0), 1)
        FROM entreprise WHERE created_at >= NOW() - INTERVAL '7 days'
        UNION ALL SELECT 'adresse_email',
            ROUND(100.0 * COUNT(*) FILTER (WHERE adresse_email IS NOT NULL AND adresse_email != '')
                / NULLIF(COUNT(*), 0), 1)
        FROM entreprise WHERE created_at >= NOW() - INTERVAL '7 days'
        
    """)
    rows = db.execute(query).fetchall()
    return [DataQualityItem(
        field_name=row.field_name,
        fill_rate=float(row.fill_rate or 0)
    ) for row in rows]

@router.get("/data-quality-boamp", response_model=List[DataQualityItem])
def get_data_quality_boamp(db: Session = Depends(get_db)):
    """Graph 4 — taux de remplissage des champs spécifiques JSON dans info_boamp"""
    query = text("""
        SELECT
            'boamp_besoin' AS field_name,
            ROUND(100.0 * COUNT(*) FILTER (WHERE info_boamp IS NOT NULL AND info_boamp->>'besoin' IS NOT NULL AND info_boamp->>'besoin' != '')
                / NULLIF(COUNT(*) FILTER (WHERE info_boamp IS NOT NULL), 0), 1) AS fill_rate
        FROM entreprise
        WHERE created_at >= NOW() - INTERVAL '7 days'

        UNION ALL SELECT 'boamp_date_limite',
            ROUND(100.0 * COUNT(*) FILTER (WHERE info_boamp IS NOT NULL AND info_boamp->>'date_limite' IS NOT NULL AND info_boamp->>'date_limite' != '')
                / NULLIF(COUNT(*) FILTER (WHERE info_boamp IS NOT NULL), 0), 1)
        FROM entreprise WHERE created_at >= NOW() - INTERVAL '7 days'

        UNION ALL SELECT 'boamp_info_complementaire',
            ROUND(100.0 * COUNT(*) FILTER (WHERE info_boamp IS NOT NULL AND info_boamp->>'info_complementaire' IS NOT NULL AND info_boamp->>'info_complementaire' != '')
                / NULLIF(COUNT(*) FILTER (WHERE info_boamp IS NOT NULL), 0), 1)
        FROM entreprise WHERE created_at >= NOW() - INTERVAL '7 days'
        UNION ALL SELECT 'boamp_info_lienOffre',
            ROUND(100.0 * COUNT(*) FILTER (WHERE info_boamp IS NOT NULL AND info_boamp->>'lienOffre' IS NOT NULL AND info_boamp->>'lienOffre' != '')
                / NULLIF(COUNT(*) FILTER (WHERE info_boamp IS NOT NULL), 0), 1)
        FROM entreprise WHERE created_at >= NOW() - INTERVAL '7 days'
    """)
    rows = db.execute(query).fetchall()
    return [DataQualityItem(
        field_name=row.field_name,
        fill_rate=float(row.fill_rate or 0)
    ) for row in rows]

@router.get("/kpi-summary", response_model=KPISummary)
def get_kpi_summary(db: Session = Depends(get_db)):
    """KPI cards en haut du dashboard"""
    q = text("""
        SELECT
            ROUND(100.0 * COUNT(*) FILTER (WHERE state='success')
                / NULLIF(COUNT(*), 0), 1) AS global_success_rate,
            COUNT(*) AS total_runs,
            ROUND(AVG(EXTRACT(EPOCH FROM (end_date - start_date)) / 60.0), 1) AS avg_min
        FROM dag_run
        WHERE logical_date >= NOW() - INTERVAL '7 days'
          AND end_date IS NOT NULL
    """)
    row = db.execute(q).fetchone()
    return KPISummary(
        global_success_rate=float(row.global_success_rate or 0),
        total_runs_7d=row.total_runs,
        avg_pipeline_duration_min=float(row.avg_min or 0),
        data_quality_rate=0.0  # calculé séparément si besoin
    )