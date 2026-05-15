
"""
db/health.py — ETL data-readiness helpers.

These functions are intentionally read-only and side-effect-free.
They are used by:
  - GET /etl/status  (FastAPI)
  - scripts/check_etl_data.py  (CLI helper for developers)

Do NOT call these from DAGs or any write path.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from db.models import Entreprise
from db.database import SessionLocal

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
#  Core query helpers
# ─────────────────────────────────────────────────────────────

def get_entreprise_count(db: Session) -> int:
    """
    Return the number of rows in the `entreprise` table.
    Raises SQLAlchemyError on DB failure — callers must handle it.
    """
    return db.query(Entreprise).count()


def has_initial_company_data(db: Session) -> bool:
    """
    Return True when at least one row exists in `entreprise`.
    Uses LIMIT 1 — O(1) regardless of table size.
    """
    return db.query(Entreprise).limit(1).first() is not None


# ─────────────────────────────────────────────────────────────
#  High-level status dict (used by FastAPI endpoint)
# ─────────────────────────────────────────────────────────────

def get_etl_readiness_status() -> dict:
    """
    Open a fresh DB session, query the entreprise table, and return a
    structured readiness dict.  The session is always closed, even on error.

    Returns one of three shapes:

    1. Data present:
       {
           "status": "ok",
           "database_connected": True,
           "entreprise_count": 1244,
           "initial_load_required": False,
           "message": "ETL data is already available."
       }

    2. Table empty:
       {
           "status": "ok",
           "database_connected": True,
           "entreprise_count": 0,
           "initial_load_required": True,
           "message": "No company data found. Trigger Airflow DAG initial_load manually."
       }

    3. DB unreachable:
       {
           "status": "error",
           "database_connected": False,
           "entreprise_count": None,
           "initial_load_required": None,
           "message": "Database connection failed."
       }
    """
    db = SessionLocal()
    try:
        count = get_entreprise_count(db)
        if count > 0:
            return {
                "status": "ok",
                "database_connected": True,
                "entreprise_count": count,
                "initial_load_required": False,
                "message": "ETL data is already available.",
            }
        else:
            return {
                "status": "ok",
                "database_connected": True,
                "entreprise_count": 0,
                "initial_load_required": True,
                "message": (
                    "No company data found. "
                    "Trigger Airflow DAG initial_load manually via "
                    "http://localhost:8080 or POST /etl/trigger-initial-load."
                ),
            }
    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("[ETL HEALTH] DB connection failed: %s", exc)
        return {
            "status": "error",
            "database_connected": False,
            "entreprise_count": None,
            "initial_load_required": None,
            "message": "Database connection failed.",
        }
    finally:
        db.close()
