from __future__ import annotations

import pandas as pd


def build_notifications(previous_scores: pd.DataFrame, previous_features: pd.DataFrame, scored: pd.DataFrame) -> pd.DataFrame:
    if scored.empty:
        return pd.DataFrame()

    reference_date = pd.to_datetime(scored["last_visit_date"]).max()
    previous_scores = previous_scores.set_index("full_visitor_id") if not previous_scores.empty else pd.DataFrame()
    previous_features = previous_features.set_index("full_visitor_id") if not previous_features.empty else pd.DataFrame()

    rows = []
    for record in scored.to_dict(orient="records"):
        visitor_id = record["full_visitor_id"]
        old_score = None
        old_segment = None
        old_last_visit = None
        if not previous_scores.empty and visitor_id in previous_scores.index:
            old_score = previous_scores.loc[visitor_id].get("lead_score_100")
            old_segment = previous_scores.loc[visitor_id].get("segment")
        if not previous_features.empty and visitor_id in previous_features.index:
            old_last_visit = previous_features.loc[visitor_id].get("last_visit_date")

        new_score = float(record["lead_score_100"])
        new_segment = record["segment"]
        last_visit_date = record.get("last_visit_date")
        is_daily_scope = pd.to_datetime(last_visit_date) == reference_date

        def add(notification_type: str, message: str):
            if not is_daily_scope:
                return
            rows.append(
                {
                    "full_visitor_id": visitor_id,
                    "notification_type": notification_type,
                    "message": message,
                    "old_score": old_score,
                    "new_score": new_score,
                    "old_segment": old_segment,
                    "new_segment": new_segment,
                    "last_visit_date": last_visit_date,
                    "is_read": False,
                }
            )

        if old_last_visit is None or pd.isna(old_last_visit) or pd.to_datetime(last_visit_date) > pd.to_datetime(old_last_visit):
            add("NEW_VISIT", f"Nouvelle visite detectee pour le lead {visitor_id}.")
        if old_score is not None and not pd.isna(old_score) and abs(float(old_score) - new_score) >= 1:
            add("SCORE_CHANGED", f"Score modifie pour le lead {visitor_id}: {old_score} -> {new_score}.")
        if old_segment and old_segment != new_segment:
            add("SEGMENT_CHANGED", f"Segment modifie pour le lead {visitor_id}: {old_segment} -> {new_segment}.")
        if old_segment != "HOT" and new_segment == "HOT":
            add("BECAME_HOT", f"Le lead {visitor_id} devient HOT.")
        if int(record.get("suspicious_activity") or 0) == 1:
            add("SUSPICIOUS_ACTIVITY", f"Activite suspecte detectee pour le lead {visitor_id}.")

    return pd.DataFrame(rows)
