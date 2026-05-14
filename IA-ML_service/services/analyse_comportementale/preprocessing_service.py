from __future__ import annotations

import json
from datetime import timezone
from typing import Any

import pandas as pd


TEXT_MISSING_VALUES = {
    "",
    "(not set)",
    "not available in demo dataset",
    "not available",
    "nan",
    "none",
    "null",
}


def parse_jsonish(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None or pd.isna(value):
        return {}
    try:
        parsed = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def clean_text(value: Any, default: str = "Non disponible") -> str:
    if value is None or pd.isna(value):
        return default
    cleaned = str(value).strip()
    if cleaned.casefold() in TEXT_MISSING_VALUES:
        return default
    return cleaned


def numeric_series(frame: pd.DataFrame, column: str, default: float = 0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default)


def normalize_train_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    frame = chunk.copy()

    device_values = frame.get("device", pd.Series({}, index=frame.index)).map(parse_jsonish)
    geo_values = frame.get("geoNetwork", pd.Series({}, index=frame.index)).map(parse_jsonish)
    totals_values = frame.get("totals", pd.Series({}, index=frame.index)).map(parse_jsonish)
    traffic_values = frame.get("trafficSource", pd.Series({}, index=frame.index)).map(parse_jsonish)

    full_visitor_id = frame.get("fullVisitorId", pd.Series("", index=frame.index)).astype(str).str.strip()
    visit_id = numeric_series(frame, "visitId").astype("Int64")
    visit_number = numeric_series(frame, "visitNumber").astype("Int64")
    visit_start_epoch = numeric_series(frame, "visitStartTime")
    visit_start_time = pd.to_datetime(visit_start_epoch, unit="s", errors="coerce", utc=True)
    visit_date = pd.to_datetime(frame.get("date", pd.Series("", index=frame.index)).astype(str), format="%Y%m%d", errors="coerce")

    session_id = frame.get("sessionId", pd.Series("", index=frame.index)).astype(str).str.strip()
    fallback_session_id = full_visitor_id + "_" + visit_id.astype(str)
    session_id = session_id.mask(session_id.isin(["", "nan", "None"]), fallback_session_id)

    normalized = pd.DataFrame(
        {
            "full_visitor_id": full_visitor_id,
            "visit_id": visit_id,
            "session_id": session_id,
            "visit_number": visit_number,
            "visit_start_time": visit_start_time.dt.tz_convert(timezone.utc).dt.to_pydatetime(),
            "visit_date": visit_date.dt.date,
            "visit_hour": visit_start_time.dt.hour.astype("Int64"),
            "device_category": device_values.map(lambda value: clean_text(value.get("deviceCategory"))),
            "browser": device_values.map(lambda value: clean_text(value.get("browser"))),
            "operating_system": device_values.map(lambda value: clean_text(value.get("operatingSystem"))),
            "country": geo_values.map(lambda value: clean_text(value.get("country"))),
            "city": geo_values.map(lambda value: clean_text(value.get("city"))),
            "traffic_source": traffic_values.map(lambda value: clean_text(value.get("source"))),
            "totals_pageviews": totals_values.map(lambda value: value.get("pageviews", 0)),
            "totals_hits": totals_values.map(lambda value: value.get("hits", 0)),
            "totals_bounces": totals_values.map(lambda value: value.get("bounces", 0)),
            "total_time_on_site": totals_values.map(lambda value: value.get("timeOnSite", 0)),
        }
    )

    for column in ["totals_pageviews", "totals_hits", "totals_bounces", "total_time_on_site"]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0).clip(lower=0)

    normalized["totals_pageviews"] = normalized["totals_pageviews"].astype(int)
    normalized["totals_hits"] = normalized["totals_hits"].astype(int)
    normalized["totals_bounces"] = (normalized["totals_bounces"] > 0).astype(int)
    normalized["total_time_on_site"] = normalized["total_time_on_site"].astype(float)

    normalized = normalized[normalized["full_visitor_id"].ne("") & normalized["session_id"].ne("")]
    normalized = normalized.drop_duplicates(subset=["full_visitor_id", "session_id"], keep="last")
    return normalized
