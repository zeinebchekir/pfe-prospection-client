"""Truncate all ETL tables cleanly."""
import sys
sys.path.insert(0, "/opt/airflow/ETL_pipeline")
from db.database import engine
from sqlalchemy import text

with engine.begin() as conn:   # begin() auto-commits on exit
    conn.execute(text("TRUNCATE TABLE entreprise, raw_leads, sync_state RESTART IDENTITY CASCADE"))
    print("All ETL tables truncated OK.")
