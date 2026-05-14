from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from psycopg2.extras import execute_values
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert

from core.db import engine
from models.analyse_comportementale import (
    Base,
    LeadBehaviorFeature,
    LeadNotification,
    LeadScore,
    LeadSessionRaw,
    LeadsActivity,
)

from .aggregation_service import build_behavior_features
from .notification_service import build_notifications
from .preprocessing_service import normalize_train_chunk
from .scoring_service import score_behavior_features


DEFAULT_CHUNK_SIZE = 50_000


def create_tables() -> None:
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_lead_scores_score_desc ON public.lead_scores (lead_score_100 DESC, rank_position ASC);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_lead_scores_segment ON public.lead_scores (segment);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_lead_sessions_raw_visitor_time ON public.lead_sessions_raw (full_visitor_id, visit_start_time DESC NULLS LAST, id DESC);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_lead_sessions_raw_visit_date ON public.lead_sessions_raw (visit_date);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_lead_behavior_features_last_visit ON public.lead_behavior_features (last_visit_date);"))


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.where(pd.notna(frame), None).to_dict(orient="records")


def _upsert_activity(records: list[dict[str, Any]]) -> None:
    if not records:
        return

    columns = [
        "full_visitor_id",
        "visit_id",
        "session_id",
        "visit_number",
        "visit_start_time",
        "visit_date",
        "visit_hour",
        "device_category",
        "browser",
        "operating_system",
        "country",
        "city",
        "traffic_source",
        "totals_pageviews",
        "totals_hits",
        "totals_bounces",
        "total_time_on_site",
    ]
    values = [tuple(record.get(column) for column in columns) for record in records]
    column_sql = ", ".join(columns)
    update_sql = ", ".join(
        f"{column} = EXCLUDED.{column}"
        for column in columns
        if column not in {"session_id"}
    )

    raw_connection = engine.raw_connection()
    try:
        cursor = raw_connection.cursor()
        execute_values(
            cursor,
            f"""
            INSERT INTO public.leads_activity ({column_sql})
            VALUES %s
            ON CONFLICT (session_id) DO UPDATE SET
                {update_sql},
                updated_at = NOW()
            """,
            values,
            page_size=10_000,
        )
        execute_values(
            cursor,
            f"""
            INSERT INTO public.lead_sessions_raw ({column_sql})
            VALUES %s
            ON CONFLICT (session_id) DO NOTHING
            """,
            values,
            page_size=10_000,
        )
        raw_connection.commit()
    except Exception:
        raw_connection.rollback()
        raise
    finally:
        raw_connection.close()


def import_train_csv(csv_path: str | Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> dict[str, int]:
    create_tables()
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {csv_path}")

    with engine.begin() as connection:
        existing_rows = connection.execute(select(func.count()).select_from(LeadSessionRaw.__table__)).scalar_one()
    skiprows = range(1, existing_rows + 1) if existing_rows else None
    if existing_rows:
        print(f"Reprise import: {existing_rows} sessions deja presentes, lecture de la suite du CSV.", flush=True)

    imported_rows = 0
    for chunk_number, chunk in enumerate(
        pd.read_csv(csv_path, chunksize=chunk_size, dtype=str, low_memory=False, skiprows=skiprows),
        start=1,
    ):
        normalized = normalize_train_chunk(chunk)
        records = _records(normalized)
        _upsert_activity(records)
        imported_rows += len(records)
        print(f"Chunk {chunk_number}: {len(records)} sessions traitees ({imported_rows} total).", flush=True)

    return {"imported_rows": imported_rows}


def _read_table(table_name: str, columns: list[str] | None = None) -> pd.DataFrame:
    selected = ", ".join(columns) if columns else "*"
    connection = engine.raw_connection()
    try:
        return pd.read_sql_query(f"SELECT {selected} FROM public.{table_name}", connection)
    finally:
        connection.close()


def _upsert_features(features: pd.DataFrame) -> None:
    if features.empty:
        return

    columns = [
        "full_visitor_id",
        "nombre_sessions",
        "total_pageviews",
        "avg_pageviews_per_session",
        "total_hits",
        "avg_hits_per_session",
        "total_bounces",
        "bounce_rate",
        "total_time_on_site",
        "avg_time_on_site",
        "first_visit_date",
        "last_visit_date",
        "days_since_last_visit",
        "recency_score",
        "suspicious_activity",
    ]
    records = _records(features[columns])
    values = [tuple(record.get(column) for column in columns) for record in records]
    column_sql = ", ".join(columns)
    update_sql = ", ".join(
        f"{column} = EXCLUDED.{column}"
        for column in columns
        if column != "full_visitor_id"
    )

    raw_connection = engine.raw_connection()
    try:
        cursor = raw_connection.cursor()
        execute_values(
            cursor,
            f"""
            INSERT INTO public.lead_behavior_features ({column_sql})
            VALUES %s
            ON CONFLICT (full_visitor_id) DO UPDATE SET
                {update_sql},
                updated_at = NOW()
            """,
            values,
            page_size=10_000,
        )
        raw_connection.commit()
    except Exception:
        raw_connection.rollback()
        raise
    finally:
        raw_connection.close()


def _upsert_scores(scored: pd.DataFrame) -> None:
    if scored.empty:
        return

    columns = [
        "full_visitor_id",
        "lead_score",
        "lead_score_100",
        "segment",
        "rank_position",
        "nombre_sessions_raw",
        "avg_hits_per_session_raw",
        "avg_pageviews_per_session_raw",
        "bounce_rate_raw",
        "recency_score_raw",
        "nombre_sessions_scaled",
        "avg_hits_per_session_scaled",
        "avg_pageviews_per_session_scaled",
        "bounce_score",
        "suspicious_activity",
    ]
    records = _records(scored[columns])
    values = [tuple(record.get(column) for column in columns) for record in records]
    column_sql = ", ".join(columns)
    update_sql = ", ".join(
        f"{column} = EXCLUDED.{column}"
        for column in columns
        if column != "full_visitor_id"
    )

    raw_connection = engine.raw_connection()
    try:
        cursor = raw_connection.cursor()
        execute_values(
            cursor,
            f"""
            INSERT INTO public.lead_scores ({column_sql})
            VALUES %s
            ON CONFLICT (full_visitor_id) DO UPDATE SET
                {update_sql},
                scored_at = NOW()
            """,
            values,
            page_size=10_000,
        )
        raw_connection.commit()
    except Exception:
        raw_connection.rollback()
        raise
    finally:
        raw_connection.close()


def _insert_notifications(notifications: pd.DataFrame) -> None:
    if notifications.empty:
        return

    columns = [
        "full_visitor_id",
        "notification_type",
        "message",
        "old_score",
        "new_score",
        "old_segment",
        "new_segment",
        "last_visit_date",
        "is_read",
    ]
    records = _records(notifications[columns])
    values = [tuple(record.get(column) for column in columns) for record in records]
    column_sql = ", ".join(columns)

    raw_connection = engine.raw_connection()
    try:
        cursor = raw_connection.cursor()
        execute_values(
            cursor,
            f"""
            INSERT INTO public.lead_notifications ({column_sql})
            VALUES %s
            ON CONFLICT (full_visitor_id, notification_type, last_visit_date) DO NOTHING
            """,
            values,
            page_size=10_000,
        )
        raw_connection.commit()
    except Exception:
        raw_connection.rollback()
        raise
    finally:
        raw_connection.close()


def recalculate_behavior() -> dict[str, int]:
    create_tables()

    previous_scores = _read_table("lead_scores", ["full_visitor_id", "lead_score_100", "segment"])
    previous_features = _read_table("lead_behavior_features", ["full_visitor_id", "last_visit_date"])
    sessions = _read_table("lead_sessions_raw")
    features = build_behavior_features(sessions)
    scored = score_behavior_features(features)

    _upsert_features(features)
    notifications = build_notifications(previous_scores, previous_features, scored)
    _upsert_scores(scored)
    _insert_notifications(notifications)

    return {
        "sessions": int(len(sessions)),
        "features": int(len(features)),
        "scores": int(len(scored)),
        "notifications": int(len(notifications)),
    }


def initialize_from_csv(csv_path: str | Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> dict[str, int]:
    create_tables()
    imported = import_train_csv(csv_path, chunk_size=chunk_size)
    recalculated = recalculate_behavior()
    return imported | recalculated


def has_activity_data() -> bool:
    create_tables()
    with engine.begin() as connection:
        count = connection.execute(select(func.count()).select_from(LeadSessionRaw.__table__)).scalar_one()
    return bool(count)
