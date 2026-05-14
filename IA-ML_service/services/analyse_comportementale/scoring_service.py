from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from .segmentation_service import segment_score


POSITIVE_FEATURES = [
    "nombre_sessions",
    "total_pageviews",
    "avg_pageviews_per_session",
    "total_hits",
    "avg_hits_per_session",
]

CLIP_LIMITS = {
    "nombre_sessions": 50,
    "total_pageviews": 500,
    "avg_pageviews_per_session": 15,
    "total_hits": 800,
    "avg_hits_per_session": 20,
}


def score_behavior_features(features: pd.DataFrame) -> pd.DataFrame:
    scoring = features.copy()
    if scoring.empty:
        return pd.DataFrame()

    for column in POSITIVE_FEATURES + ["bounce_rate", "recency_score"]:
        scoring[f"{column}_raw"] = scoring[column]

    for column in POSITIVE_FEATURES:
        scoring[column] = pd.to_numeric(scoring[column], errors="coerce").fillna(0).clip(lower=0)

    scoring["bounce_rate"] = pd.to_numeric(scoring["bounce_rate"], errors="coerce").fillna(1).clip(0, 1)
    scoring["recency_score"] = pd.to_numeric(scoring["recency_score"], errors="coerce").fillna(0).clip(0, 100)
    scoring["suspicious_activity"] = (
        (scoring["avg_hits_per_session_raw"] > 30)
        | (scoring["avg_pageviews_per_session_raw"] > 20)
        | ((scoring["bounce_rate_raw"] == 0) & (scoring["avg_hits_per_session_raw"] > 35))
    ).astype(int)

    scoring_input = scoring[POSITIVE_FEATURES].copy()
    for column, upper_limit in CLIP_LIMITS.items():
        scoring_input[column] = scoring_input[column].clip(upper=upper_limit)

    for column in POSITIVE_FEATURES:
        scoring_input[column] = np.log1p(scoring_input[column])

    scaled_values = MinMaxScaler(feature_range=(0, 100)).fit_transform(scoring_input)
    for index, column in enumerate(POSITIVE_FEATURES):
        scoring[f"{column}_scaled"] = scaled_values[:, index]

    scoring["bounce_score"] = (1 - scoring["bounce_rate"]) * 100
    scoring["lead_score"] = (
        scoring["recency_score"] * 0.25
        + scoring["avg_hits_per_session_scaled"] * 0.20
        + scoring["nombre_sessions_scaled"] * 0.20
        + scoring["avg_pageviews_per_session_scaled"] * 0.20
        + scoring["bounce_score"] * 0.15
    )
    scoring.loc[scoring["nombre_sessions_raw"] <= 1, "lead_score"] *= 0.90
    scoring.loc[scoring["suspicious_activity"] == 1, "lead_score"] *= 0.80

    scoring["lead_score_100"] = scoring["lead_score"].clip(0, 100).round(1)
    scoring = scoring.sort_values("lead_score_100", ascending=False).reset_index(drop=True)
    scoring["rank_position"] = scoring.index + 1
    scoring["segment"] = scoring["lead_score_100"].map(segment_score)
    return scoring
