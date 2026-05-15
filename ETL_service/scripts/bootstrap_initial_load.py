#!/usr/bin/env python3
"""
ETL Bootstrap Service  —  production-ready startup guard
=========================================================
Ensures `initial_load` DAG runs exactly once when `entreprise` is empty.

State machine covers every scenario:

  Case A  entreprise has rows          → skip, exit OK
  Case B  empty + no active run        → trigger
  Case C  empty + recently queued run  → wait/poll
  Case D  empty + stale queued run     → mark failed, re-trigger
  Case E  empty + run is running       → poll (or exit if WAIT=false)
  Case F  empty + previous run failed  → re-trigger
  Case G  run succeeded but table empty→ treat as incomplete, re-trigger

Environment variables
---------------------
  DATABASE_URL                         ETL PostgreSQL DSN
  AIRFLOW_URL                          Airflow base URL (log messages only)
  BOOTSTRAP_WAIT_FOR_INITIAL_LOAD      "true" to block until DAG finishes
  BOOTSTRAP_INITIAL_LOAD_TIMEOUT_SECONDS  Polling timeout (default 3600)
  BOOTSTRAP_STALE_QUEUED_SECONDS       Seconds before a queued run is stale (default 300)
  BOOTSTRAP_RESET_STALE_DAGRUNS        "true" to auto-clean stale runs (default true)
  BOOTSTRAP_MAX_TRIGGER_ATTEMPTS       Max trigger attempts (default 2)
"""

import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional

sys.path.insert(0, "/opt/airflow/ETL_pipeline")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BOOTSTRAP] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger("bootstrap")

# ── Config ─────────────────────────────────────────────────────────────────────
DATABASE_URL   = os.environ.get("DATABASE_URL",
                    os.environ.get("ETL_DATABASE_URL",
                        "postgresql://airflow:airflow@postgres-airflow/airflow"))
AIRFLOW_URL    = os.environ.get("AIRFLOW_URL", "http://airflow-apiserver:8080")
WAIT_FOR_LOAD  = os.environ.get("BOOTSTRAP_WAIT_FOR_INITIAL_LOAD",      "true").lower()  == "true"
LOAD_TIMEOUT   = int(os.environ.get("BOOTSTRAP_INITIAL_LOAD_TIMEOUT_SECONDS", "3600"))
STALE_SECONDS  = int(os.environ.get("BOOTSTRAP_STALE_QUEUED_SECONDS",         "300"))
RESET_STALE    = os.environ.get("BOOTSTRAP_RESET_STALE_DAGRUNS",         "true").lower() == "true"
MAX_ATTEMPTS   = int(os.environ.get("BOOTSTRAP_MAX_TRIGGER_ATTEMPTS",          "2"))
DAG_ID         = "initial_load"

DB_RETRIES  = 60
DB_INTERVAL = 5   # seconds


# ── Data model ─────────────────────────────────────────────────────────────────

@dataclass
class DagRun:
    run_id:     str
    state:      str
    queued_at:  Optional[datetime]
    start_date: Optional[datetime]

    @property
    def age_seconds(self) -> float:
        """Seconds since the run was queued (or started, as fallback)."""
        ref = self.queued_at or self.start_date
        if ref is None:
            return 0.0
        now = datetime.now(timezone.utc)
        ref = ref if ref.tzinfo else ref.replace(tzinfo=timezone.utc)
        return (now - ref).total_seconds()

    @property
    def is_stale(self) -> bool:
        return self.state == "queued" and self.age_seconds > STALE_SECONDS


# ══════════════════════════════════════════════════════════════════════════════
#  DATABASE helpers
# ══════════════════════════════════════════════════════════════════════════════

def wait_for_db():
    from sqlalchemy import create_engine, text

    log.info("Waiting for database …")
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})

    for attempt in range(1, DB_RETRIES + 1):
        try:
            with engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            log.info("Database ready ✅  (attempt %d)", attempt)
            return engine
        except Exception as exc:
            log.warning("DB not ready [%d/%d]: %s", attempt, DB_RETRIES, exc)
            time.sleep(DB_INTERVAL)

    log.error("Database unreachable after %d attempts — aborting.", DB_RETRIES)
    sys.exit(1)


def ensure_tables(engine):
    try:
        from db.database import create_tables
        create_tables()
        log.info("ETL tables ensured ✅")
    except Exception as exc:
        log.warning("create_tables() skipped (may already exist): %s", exc)


def get_entreprise_count(engine) -> int:
    """Returns row count, or -1 if the table doesn't exist yet."""
    from sqlalchemy import text
    from sqlalchemy.exc import ProgrammingError

    try:
        with engine.begin() as conn:
            return conn.execute(text("SELECT COUNT(*) FROM entreprise")).scalar()
    except ProgrammingError:
        return -1
    except Exception as exc:
        log.error("Error counting entreprise: %s", exc)
        return -1


# ══════════════════════════════════════════════════════════════════════════════
#  AIRFLOW METADATA DB helpers  (direct SQL — no HTTP auth needed)
# ══════════════════════════════════════════════════════════════════════════════

def get_active_dag_runs(engine) -> List[DagRun]:
    """
    Return all DAG runs for initial_load that are queued or running.
    Queries the Airflow metadata DB directly — avoids REST API auth issues.
    """
    from sqlalchemy import text

    try:
        with engine.begin() as conn:
            rows = conn.execute(
                text(
                    "SELECT run_id, state, queued_at, start_date "
                    "FROM dag_run "
                    "WHERE dag_id = :dag_id "
                    "  AND state IN ('queued', 'running') "
                    "ORDER BY queued_at DESC NULLS LAST"
                ),
                {"dag_id": DAG_ID},
            ).fetchall()

        runs = []
        for row in rows:
            runs.append(DagRun(
                run_id     = row[0],
                state      = row[1],
                queued_at  = row[2],
                start_date = row[3],
            ))
        return runs

    except Exception as exc:
        log.warning("Could not query dag_run table: %s", exc)
        return []


def get_dag_run_state(engine, run_id: str) -> Optional[str]:
    """Return the current state of a specific DAG run."""
    from sqlalchemy import text

    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT state FROM dag_run WHERE dag_id = :d AND run_id = :r"),
                {"d": DAG_ID, "r": run_id},
            ).fetchone()
        return row[0] if row else None
    except Exception as exc:
        log.warning("Could not get DAG run state: %s", exc)
        return None


def mark_dag_run_failed(engine, run_id: str) -> bool:
    """
    Mark a stale queued run as 'failed' so the scheduler ignores it.
    This is safer than DELETE — it preserves history and releases the slot.
    Only affects runs that are still in 'queued' state.
    """
    from sqlalchemy import text

    try:
        with engine.begin() as conn:
            result = conn.execute(
                text(
                    "UPDATE dag_run "
                    "SET state = 'failed', end_date = NOW() "
                    "WHERE dag_id = :dag_id "
                    "  AND run_id = :run_id "
                    "  AND state = 'queued'"
                ),
                {"dag_id": DAG_ID, "run_id": run_id},
            )
        if result.rowcount > 0:
            log.info("Stale run '%s' marked as failed ✅", run_id)
            return True
        else:
            log.warning("Run '%s' was not in queued state — skipping mark-failed.", run_id)
            return False
    except Exception as exc:
        log.error("Failed to mark run as failed: %s", exc)
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  CELERY WORKER readiness  (Airflow 3 — CLI subcommand removed)
# ══════════════════════════════════════════════════════════════════════════════

def _celery_ping() -> bool:
    try:
        from airflow.providers.celery.executors.celery_executor import app as celery_app
        result = celery_app.control.inspect(timeout=8).ping()
        if result:
            log.info("Celery worker(s) alive: %s ✅", list(result.keys()))
            return True
    except Exception as exc:
        log.debug("Celery ping error: %s", exc)
    return False


def wait_for_worker(max_wait: int = 180, interval: int = 10):
    log.info("Verifying Celery worker is accepting tasks (max %ds) …", max_wait)
    deadline = time.time() + max_wait
    while time.time() < deadline:
        if _celery_ping():
            return True
        log.info("Worker not yet responding — %ds remaining …", int(deadline - time.time()))
        time.sleep(interval)
    log.warning(
        "Worker did not respond within %ds. Proceeding anyway — "
        "if DAG stays queued, check: docker compose logs -f airflow-worker",
        max_wait,
    )
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  AIRFLOW CLI helpers  (trigger, unpause — no HTTP auth needed)
# ══════════════════════════════════════════════════════════════════════════════

def unpause_dag():
    result = subprocess.run(
        ["airflow", "dags", "unpause", DAG_ID],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        log.info("DAG '%s' unpaused ✅", DAG_ID)
    else:
        log.warning("unpause warning (non-fatal): %s", result.stderr.strip())


def trigger_dag(attempt: int) -> Optional[str]:
    run_id = f"auto_initial_load_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    conf   = (
        f'{{"triggered_by":"etl-bootstrap","reason":"entreprise table empty",'
        f'"bootstrap_attempt":{attempt}}}'
    )
    log.info("Triggering %s (attempt %d/%d) — run_id=%s", DAG_ID, attempt, MAX_ATTEMPTS, run_id)

    for retry in range(1, 4):
        result = subprocess.run(
            ["airflow", "dags", "trigger", DAG_ID, "--run-id", run_id, "--conf", conf],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            log.info("✅ DAG triggered successfully! run_id=%s", run_id)
            log.info("   Follow:    docker compose logs -f airflow-worker")
            log.info("   Airflow:   %s/dags/%s/runs", AIRFLOW_URL, DAG_ID)
            return run_id

        combined = result.stderr + result.stdout
        if "already exists" in combined:
            log.info("Run ID already exists — treating as successful trigger.")
            return run_id

        log.warning("Trigger retry %d/3 failed: %s", retry, combined.strip())
        time.sleep(5)

    log.error("All trigger retries failed. Try manually: Airflow UI → %s", AIRFLOW_URL)
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  POLLING
# ══════════════════════════════════════════════════════════════════════════════

# Return values from poll_run_until_done
POLL_SUCCESS    = "success"
POLL_FAILED     = "failed"
POLL_STALE      = "stale"
POLL_INCOMPLETE = "incomplete"
POLL_TIMEOUT    = "timeout"


def poll_run_until_done(run_id: str, engine) -> str:
    """
    Poll a DAG run until it reaches a terminal state or timeout.

    Returns one of: success | failed | stale | incomplete | timeout
    """
    log.info(
        "Polling run '%s' every 10s (timeout %ds, stale threshold %ds) …",
        run_id, LOAD_TIMEOUT, STALE_SECONDS,
    )
    deadline     = time.time() + LOAD_TIMEOUT
    queued_since : Optional[float] = None
    warned_stale = False

    while time.time() < deadline:
        state = get_dag_run_state(engine, run_id)

        if state is None:
            log.warning("Could not read run state — retrying in 10s …")
        elif state == "success":
            log.info("Polling: run_id=%s state=success", run_id)
            return POLL_SUCCESS
        elif state in ("failed", "upstream_failed", "removed"):
            log.warning("Polling: run_id=%s state=%s", run_id, state)
            return POLL_FAILED
        elif state == "queued":
            if queued_since is None:
                queued_since = time.time()
            age = time.time() - queued_since
            log.info("Polling: run_id=%s state=queued age=%.0fs", run_id, age)
            if age > STALE_SECONDS and not warned_stale:
                log.warning(
                    "[WARN] Run stuck in queued for >%ds — "
                    "scheduler/worker may be unavailable. Run:\n"
                    "  docker compose logs -f airflow-scheduler\n"
                    "  docker compose logs -f airflow-worker",
                    STALE_SECONDS,
                )
                warned_stale = True
            if age > STALE_SECONDS:
                return POLL_STALE
        elif state == "running":
            queued_since = None  # reset stale counter
            log.info(
                "Polling: run_id=%s state=running | %ds remaining",
                run_id, int(deadline - time.time()),
            )
        else:
            log.info("Polling: run_id=%s state=%s", run_id, state)

        time.sleep(10)

    log.warning("Timeout (%ds) waiting for run '%s'. Check Airflow UI: %s",
                LOAD_TIMEOUT, run_id, AIRFLOW_URL)
    return POLL_TIMEOUT


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN STATE MACHINE
# ══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    log.info("=" * 60)
    log.info("  ETL BOOTSTRAP — AUTO INITIAL LOAD GUARD")
    log.info("  Config: WAIT=%s | STALE=%ds | RESET_STALE=%s | MAX_ATTEMPTS=%d",
             WAIT_FOR_LOAD, STALE_SECONDS, RESET_STALE, MAX_ATTEMPTS)
    log.info("=" * 60)

    # ── Step 1: Infrastructure readiness ─────────────────────────
    engine = wait_for_db()
    ensure_tables(engine)
    wait_for_worker(max_wait=180, interval=10)

    # ── Step 2: Check if data already exists ─────────────────────
    count = get_entreprise_count(engine)
    if count == -1:
        log.warning("Table 'entreprise' not found yet — waiting 20s for airflow-init …")
        time.sleep(20)
        count = get_entreprise_count(engine)

    log.info("entreprise rows: %d", count)

    if count > 0:
        log.info("✅ entreprise already has %d rows — nothing to do.", count)
        log.info("=" * 60)
        return 0

    # ── Step 3: State-machine loop ───────────────────────────────
    log.info("entreprise is EMPTY — entering bootstrap state machine …")
    unpause_dag()

    attempts = 0

    while attempts < MAX_ATTEMPTS:
        active_runs = get_active_dag_runs(engine)

        # ── Log active runs overview ──────────────────────────────
        if active_runs:
            log.info("Active initial_load runs found: %d", len(active_runs))
            for r in active_runs:
                log.info(
                    "  run_id=%-45s state=%-10s age=%.0fs",
                    r.run_id, r.state, r.age_seconds,
                )
        else:
            log.info("No active initial_load runs found.")

        # ── No active run → trigger ───────────────────────────────
        if not active_runs:
            attempts += 1
            run_id = trigger_dag(attempts)
            if run_id is None:
                log.error("Trigger failed. Retrying if attempts remain.")
                time.sleep(15)
                continue

            if not WAIT_FOR_LOAD:
                log.info("BOOTSTRAP_WAIT_FOR_INITIAL_LOAD=false — exiting after trigger.")
                log.info("=" * 60)
                return 0

            # Wait and then re-evaluate
            result = poll_run_until_done(run_id, engine)
            count  = get_entreprise_count(engine)
            log.info("entreprise rows after DAG: %d", count)

            if result == POLL_SUCCESS and count > 0:
                log.info("✅ Initial load completed successfully! (%d rows)", count)
                log.info("=" * 60)
                return 0

            if result == POLL_SUCCESS and count == 0:
                log.warning(
                    "DAG reported success but entreprise is still empty — "
                    "treating as incomplete (Case G)."
                )
                # Fall through to retry loop
                continue

            if result in (POLL_FAILED, POLL_INCOMPLETE):
                log.warning("DAG %s — retrying if attempts remain.", result)
                time.sleep(10)
                continue

            if result in (POLL_STALE, POLL_TIMEOUT):
                log.warning("DAG %s after trigger — manual investigation required.", result)
                # Don't retry indefinitely on timeout
                break

            continue  # unexpected result → retry

        # ── Has active run(s) — evaluate each ────────────────────
        handled = False
        for run in active_runs:

            # ── RUNNING ──────────────────────────────────────────
            if run.state == "running":
                log.info("initial_load is already RUNNING (run_id=%s).", run.run_id)

                if not WAIT_FOR_LOAD:
                    log.info("BOOTSTRAP_WAIT_FOR_INITIAL_LOAD=false — exiting.")
                    log.info("=" * 60)
                    return 0

                result = poll_run_until_done(run.run_id, engine)
                count  = get_entreprise_count(engine)
                log.info("entreprise rows after DAG: %d", count)

                if result == POLL_SUCCESS and count > 0:
                    log.info("✅ Initial load completed successfully! (%d rows)", count)
                    log.info("=" * 60)
                    return 0
                if result == POLL_SUCCESS and count == 0:
                    log.warning("DAG succeeded but table still empty — treating as incomplete.")
                    handled = True
                    break  # break inner loop → re-evaluate active_runs
                if result in (POLL_FAILED, POLL_INCOMPLETE):
                    log.warning("Running DAG %s — will retry.", result)
                    handled = True
                    break
                if result in (POLL_STALE, POLL_TIMEOUT):
                    log.warning("Running DAG %s — manual check required.", result)
                    log.info("=" * 60)
                    return 1  # exit with error; needs human intervention

            # ── QUEUED ───────────────────────────────────────────
            elif run.state == "queued":
                if run.is_stale:
                    log.info(
                        "STALE queued run detected: run_id=%s age=%.0fs (threshold=%ds)",
                        run.run_id, run.age_seconds, STALE_SECONDS,
                    )
                    if not RESET_STALE:
                        log.error(
                            "BOOTSTRAP_RESET_STALE_DAGRUNS=false — "
                            "cannot auto-clean. Please investigate manually."
                        )
                        log.info("=" * 60)
                        return 1

                    log.info("Marking stale run as failed to unblock scheduler …")
                    mark_dag_run_failed(engine, run.run_id)
                    time.sleep(5)  # let scheduler notice
                    handled = True
                    break  # re-evaluate outer loop

                else:
                    # Fresh queued run — give it a chance
                    log.info(
                        "Recently queued run (age=%.0fs < threshold=%ds) — waiting …",
                        run.age_seconds, STALE_SECONDS,
                    )

                    if not WAIT_FOR_LOAD:
                        log.info("BOOTSTRAP_WAIT_FOR_INITIAL_LOAD=false — "
                                 "assuming this run will execute. Exiting.")
                        log.info("=" * 60)
                        return 0

                    result = poll_run_until_done(run.run_id, engine)
                    count  = get_entreprise_count(engine)
                    log.info("entreprise rows after DAG: %d", count)

                    if result == POLL_SUCCESS and count > 0:
                        log.info("✅ Initial load completed successfully! (%d rows)", count)
                        log.info("=" * 60)
                        return 0
                    if result == POLL_SUCCESS and count == 0:
                        log.warning("DAG succeeded but table still empty — treating as incomplete.")
                        handled = True
                        break
                    if result == POLL_STALE:
                        log.warning("Queued run became stale during polling.")
                        if RESET_STALE:
                            mark_dag_run_failed(engine, run.run_id)
                        handled = True
                        break
                    if result in (POLL_FAILED, POLL_INCOMPLETE):
                        log.warning("Queued run %s.", result)
                        handled = True
                        break
                    if result == POLL_TIMEOUT:
                        log.warning("Timed out waiting. Manual check required.")
                        log.info("=" * 60)
                        return 1

        if not handled:
            # All active runs were processed without finding a clear retry path
            # Re-check entreprise count before giving up
            count = get_entreprise_count(engine)
            if count > 0:
                log.info("✅ entreprise now has %d rows — success.", count)
                log.info("=" * 60)
                return 0
            # No active runs left and count still 0 — loop will trigger
            log.info("No more active runs and table still empty — will trigger.")

        # Small delay before next iteration
        time.sleep(5)

    # ── Exhausted attempts ────────────────────────────────────────
    final_count = get_entreprise_count(engine)
    if final_count > 0:
        log.info("✅ entreprise has %d rows — success (caught on final check).", final_count)
        log.info("=" * 60)
        return 0

    log.error(
        "Bootstrap exhausted %d attempts. entreprise still empty. "
        "Investigate Airflow: %s/dags/%s",
        MAX_ATTEMPTS, AIRFLOW_URL, DAG_ID,
    )
    log.info("=" * 60)
    return 1  # non-zero exit for visibility (restart: no → won't loop)


if __name__ == "__main__":
    sys.exit(main())
