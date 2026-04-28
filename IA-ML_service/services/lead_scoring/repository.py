from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import numpy as np
import pandas as pd
from sqlalchemy import text

from core.db import engine


def load_all_opportunities() -> pd.DataFrame:
    query = "SELECT * FROM public.lead_opportunity ORDER BY last_modified_date DESC, company_name ASC"
    connection = engine.raw_connection()
    try:
        return pd.read_sql_query(query, connection)
    finally:
        connection.close()


def load_opportunity_by_id(lead_id: UUID | str) -> pd.DataFrame:
    query = "SELECT * FROM public.lead_opportunity WHERE lead_id = %(lead_id)s"
    connection = engine.raw_connection()
    try:
        return pd.read_sql_query(query, connection, params={"lead_id": str(lead_id)})
    finally:
        connection.close()


def load_latest_performance_record() -> dict[str, Any] | None:
    query = """
        SELECT
            model_name,
            model_version,
            best_model,
            stack_name,
            accuracy,
            precision,
            recall,
            f1_score,
            roc_auc,
            threshold,
            training_dataset_size,
            feature_count,
            last_training_date
        FROM public.performance_model
        ORDER BY last_training_date DESC, id DESC
        LIMIT 1
    """
    connection = engine.raw_connection()
    try:
        dataframe = pd.read_sql_query(query, connection)
    finally:
        connection.close()
    if dataframe.empty:
        return None
    record = dataframe.iloc[0].to_dict()
    return {key: _to_python(value) for key, value in record.items()}


def persist_performance_record(record: dict[str, Any]) -> None:
    statement = text(
        """
        INSERT INTO public.performance_model (
            model_name,
            model_version,
            best_model,
            stack_name,
            accuracy,
            precision,
            recall,
            f1_score,
            roc_auc,
            threshold,
            training_dataset_size,
            feature_count,
            last_training_date
        )
        VALUES (
            :model_name,
            :model_version,
            :best_model,
            :stack_name,
            :accuracy,
            :precision,
            :recall,
            :f1_score,
            :roc_auc,
            :threshold,
            :training_dataset_size,
            :feature_count,
            :last_training_date
        )
        """
    )
    with engine.begin() as connection:
        connection.execute(statement, [record])


def persist_scored_rows(scored_frame: pd.DataFrame) -> int:
    if scored_frame.empty:
        return 0

    update_sql = text(
        """
        UPDATE public.lead_opportunity
        SET
            engagement_score = :engagement_score,
            time_per_visit = :time_per_visit,
            log_visits = :log_visits,
            log_time = :log_time,
            log_pageviews = :log_pageviews,
            visits_x_time = :visits_x_time,
            high_engagement = :high_engagement,
            text_length = :text_length,
            word_count = :word_count,
            unique_words = :unique_words,
            avg_word_length = :avg_word_length,
            positive_word_count = :positive_word_count,
            negative_word_count = :negative_word_count,
            sentiment_ratio = :sentiment_ratio,
            lead_score_probability = :lead_score_probability,
            lead_score_predicted = :lead_score_predicted,
            lead_temperature = :lead_temperature,
            model_version = :model_version,
            scored_at = :scored_at
        WHERE lead_id = :lead_id
        """
    )

    payloads = []
    for row in scored_frame.reset_index(drop=True).to_dict(orient="records"):
        payloads.append({key: _to_python(value) for key, value in row.items()})

    with engine.begin() as connection:
        connection.execute(update_sql, payloads)

    return len(payloads)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_python(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return value
