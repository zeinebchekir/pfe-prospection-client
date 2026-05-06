#!/usr/bin/env python3
"""
scripts/check_etl_data.py
─────────────────────────
Developer CLI tool: check whether the ETL database has company data and
whether the `initial_load` Airflow DAG needs to be triggered.

Usage
-----
Run locally (requires DB to be reachable):

    # With the default DATABASE_URL from .env:
    python scripts/check_etl_data.py

    # Override DB URL:
    DATABASE_URL="postgresql://airflow:airflow@localhost:5433/airflow" \
        python scripts/check_etl_data.py

Run inside the etl-fastapi container:

    docker exec qualifixproject_etl_fastapi \
        python /app/../../scripts/check_etl_data.py

Or use the API (no Python needed):

    curl http://localhost:8001/etl/status

Environment variables
---------------------
DATABASE_URL   — PostgreSQL DSN for the ETL database
                 (default: postgresql://airflow:airflow@localhost:5433/airflow)
AIRFLOW_URL    — Airflow UI base URL shown in the hint
                 (default: http://localhost:8080)
"""

import os
import sys

# ── Allow running from repo root without installing the package ──
_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
_ETL_PIPELINE = os.path.join(_SCRIPT_DIR, "..", "ETL_service", "ETL_pipeline")
sys.path.insert(0, _ETL_PIPELINE)

# ── DB connection — mirrors database.py but uses a localhost port
#    (port 5433 is the external port when postgres-airflow is running in Docker)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://airflow:airflow@localhost:5433/airflow",
)
AIRFLOW_URL = os.environ.get("AIRFLOW_URL", "http://localhost:8080")
ETL_API_URL = os.environ.get("ETL_API_URL", "http://localhost:8001")

BANNER = "=" * 55


def main():
    print(BANNER)
    print("  ETL DATA READINESS CHECK")
    print(BANNER)

    # ── Import SQLAlchemy pieces after path is set ──────────────
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        from db.models import Entreprise
    except ImportError as exc:
        print(f"[ERROR] Cannot import ETL modules: {exc}")
        print(f"        Make sure ETL_pipeline is on the path: {_ETL_PIPELINE}")
        sys.exit(2)

    # ── Try to connect ──────────────────────────────────────────
    print(f"\n  DB URL  : {DATABASE_URL}")
    try:
        engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
        Session = sessionmaker(bind=engine)
        db = Session()

        # Quick connectivity ping
        db.execute(text("SELECT 1"))
        print("  DB      : ✅  Connected\n")
    except Exception as exc:
        print(f"  DB      : ❌  Connection failed\n")
        print(f"[ERROR] {exc}")
        print()
        print("  Possible causes:")
        print("    • Docker containers are not running   →  docker-compose up -d")
        print("    • Wrong DATABASE_URL                  →  check your .env")
        print("    • postgres-airflow port not exposed   →  check docker-compose.yml")
        print(BANNER)
        sys.exit(1)

    # ── Count rows ──────────────────────────────────────────────
    try:
        count = db.query(Entreprise).count()
    except Exception as exc:
        print(f"[ERROR] Could not query entreprise table: {exc}")
        print("        The table may not exist yet — did Airflow init run?")
        db.close()
        sys.exit(1)
    finally:
        db.close()

    # ── Report ──────────────────────────────────────────────────
    print(f"  Entreprise rows : {count:,}")
    print()

    if count == 0:
        print("  ⚠️  INITIAL LOAD REQUIRED")
        print()
        print("  The `entreprise` table is empty.")
        print("  You must trigger the `initial_load` Airflow DAG once.")
        print()
        print("  Option A — Airflow UI (recommended):")
        print(f"    1. Open   {AIRFLOW_URL}")
        print("    2. Login with your Airflow credentials (see .env)")
        print("    3. Find DAG `initial_load`")
        print("    4. Click the ▶ (Trigger) button")
        print("    5. Wait for all tasks to succeed (can take 10-30 min)")
        print()
        print("  Option B — ETL API (programmatic):")
        print(f"    curl -X POST {ETL_API_URL}/etl/trigger-initial-load")
        print()
        print("  Option C — Check via API:")
        print(f"    curl {ETL_API_URL}/etl/status")
    else:
        print("  ✅  INITIAL LOAD NOT REQUIRED")
        print()
        print(f"  The database already contains {count:,} company records.")
        print("  The project can run normally.")
        print()
        print("  Delta DAGs that keep the data fresh:")
        print("    • sync_datagouv  — runs every 6 hours")
        print("    • sync_boamp     — runs daily at 06:00")
        print()
        print("  If you intentionally want a full reload:")
        print(f"    curl -X POST '{ETL_API_URL}/etl/trigger-initial-load?force=true'")
        print("    ⚠️  This may cause duplicate/overwritten records — use with care.")

    print()
    print(BANNER)


if __name__ == "__main__":
    main()
