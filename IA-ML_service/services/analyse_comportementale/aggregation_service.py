from __future__ import annotations

import numpy as np
import pandas as pd


LAMBDA_DECAY = 0.03


def build_behavior_features(sessions: pd.DataFrame) -> pd.DataFrame:
    frame = sessions.copy()
    if frame.empty:
        return pd.DataFrame()

    frame["visit_date"] = pd.to_datetime(frame["visit_date"], errors="coerce")
    for column in ["totals_pageviews", "totals_hits", "totals_bounces", "total_time_on_site"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0).clip(lower=0)

    frame["is_bounce"] = (frame["totals_bounces"].fillna(0) > 0).astype(int)

    features = frame.groupby("full_visitor_id").agg(
        nombre_sessions=("session_id", "nunique"),
        total_pageviews=("totals_pageviews", "sum"),
        avg_pageviews_per_session=("totals_pageviews", "mean"),
        total_hits=("totals_hits", "sum"),
        avg_hits_per_session=("totals_hits", "mean"),
        total_bounces=("is_bounce", "sum"),
        bounce_rate=("is_bounce", "mean"),
        total_time_on_site=("total_time_on_site", "sum"),
        avg_time_on_site=("total_time_on_site", "mean"),
        first_visit_date=("visit_date", "min"),
        last_visit_date=("visit_date", "max"),
    ).reset_index()

    features["nombre_sessions"] = features["nombre_sessions"].clip(lower=1).astype(int)
    reference_date = features["last_visit_date"].max()
    features["days_since_last_visit"] = (reference_date - features["last_visit_date"]).dt.days.fillna(999).astype(int)
    features["recency_score"] = (np.exp(-LAMBDA_DECAY * features["days_since_last_visit"]) * 100).clip(0, 100)

    features["suspicious_activity"] = (
        (features["avg_hits_per_session"] > 30)
        | (features["avg_pageviews_per_session"] > 20)
        | ((features["bounce_rate"] == 0) & (features["avg_hits_per_session"] > 35))
    ).astype(int)

    features["first_visit_date"] = features["first_visit_date"].dt.date
    features["last_visit_date"] = features["last_visit_date"].dt.date
    return features
