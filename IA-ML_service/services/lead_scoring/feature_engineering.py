from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


TARGET_COLUMN = "lead_score"
TEXT_COLUMN = "interaction_history"
MISSING_CATEGORY_VALUE = "missing"
MISSING_TEXT_VALUE = "pas historique"
NULL_LIKE_VALUES = {"", "n/a", "na", "nan", "none", "null"}
NUMERIC_QUANTILE_LOW = 0.01
NUMERIC_QUANTILE_HIGH = 0.99

RAW_NUMERIC_COLUMNS = [
    "total_visits",
    "time_on_website_sec",
    "avg_page_views",
]

CATEGORICAL_COLUMNS = [
    "industry",
    "company_size",
    "annual_revenue",
    "country",
    "city",
    "lead_source",
    "last_activity",
    "last_notable_activity",
    "job_title",
]

ENGINEERED_COLUMNS = [
    "engagement_score",
    "time_per_visit",
    "log_visits",
    "log_time",
    "log_pageviews",
    "visits_x_time",
    "high_engagement",
    "text_length",
    "word_count",
    "unique_words",
    "avg_word_length",
    "positive_word_count",
    "negative_word_count",
    "sentiment_ratio",
]

ALL_NUMERIC_COLUMNS = RAW_NUMERIC_COLUMNS + ENGINEERED_COLUMNS

DISPLAY_TO_DB_COLUMNS = {
    "Lead ID": "lead_id",
    "Company Name": "company_name",
    "Contact Name": "contact_name",
    "Job Title": "job_title",
    "Email": "email",
    "Phone Number": "phone_number",
    "Website": "website",
    "Last Modified Date": "last_modified_date",
    "Industry": "industry",
    "Company Size": "company_size",
    "Annual Revenue": "annual_revenue",
    "Country": "country",
    "City": "city",
    "Lead Source": "lead_source",
    "Lead Score": TARGET_COLUMN,
    "Total Visits": "total_visits",
    "Time on Website (sec)": "time_on_website_sec",
    "Avg Page Views": "avg_page_views",
    "Last Activity": "last_activity",
    "Last Notable Activity": "last_notable_activity",
    "Interaction History": TEXT_COLUMN,
}

LEAK_PATTERN = re.compile(r"\b(signe|refuse|devis|accepte|fructueux|contrat)\b")

POSITIVE_WORDS = {
    "interesse",
    "rappeler",
    "demo",
    "reunion",
    "positif",
    "suite",
    "projet",
}

NEGATIVE_WORDS = {
    "pas",
    "jamais",
    "non",
    "annule",
    "reporte",
    "indisponible",
}


@dataclass
class PreparedFrames:
    feature_store: pd.DataFrame
    cat_frame: pd.DataFrame
    transformed_source: pd.DataFrame


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if pd.isna(value):
        return True
    normalized = _normalize_spaces(str(value)).casefold()
    return normalized in NULL_LIKE_VALUES


def _normalize_text(value: str) -> str:
    normalized = _strip_accents(value.casefold())
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    return _normalize_spaces(normalized)


def _normalize_category_value(value: Any) -> str:
    if _is_missing_value(value):
        return MISSING_CATEGORY_VALUE
    normalized = _normalize_spaces(str(value)).casefold()
    return normalized or MISSING_CATEGORY_VALUE


def _tokenize_text(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value)


def normalize_dataframe(data: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    dataframe = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    dataframe = dataframe.rename(columns={col: DISPLAY_TO_DB_COLUMNS.get(col, col) for col in dataframe.columns})

    for column in ALL_NUMERIC_COLUMNS + CATEGORICAL_COLUMNS + [TEXT_COLUMN, TARGET_COLUMN, "lead_id"]:
        if column not in dataframe.columns:
            dataframe[column] = np.nan

    return dataframe


def clean_text(value: Any) -> str:
    if _is_missing_value(value):
        return MISSING_TEXT_VALUE

    text = _normalize_text(str(value))
    text = LEAK_PATTERN.sub(" ", text)
    text = _normalize_spaces(text)
    return text or MISSING_TEXT_VALUE


def _safe_to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def build_preprocessing_state(dataframe: pd.DataFrame) -> dict[str, Any]:
    frame = normalize_dataframe(dataframe)

    numeric_frame = frame[RAW_NUMERIC_COLUMNS].apply(_safe_to_numeric)
    numeric_medians = {
        column: float(numeric_frame[column].median())
        if not np.isnan(numeric_frame[column].median())
        else 0.0
        for column in RAW_NUMERIC_COLUMNS
    }

    numeric_bounds = {}
    filled_numeric = numeric_frame.fillna(numeric_medians).clip(lower=0)
    for column in RAW_NUMERIC_COLUMNS:
        column_frame = filled_numeric[column]
        lower_bound = float(column_frame.quantile(NUMERIC_QUANTILE_LOW)) if len(column_frame) else 0.0
        upper_bound = float(column_frame.quantile(NUMERIC_QUANTILE_HIGH)) if len(column_frame) else 0.0

        if np.isnan(lower_bound):
            lower_bound = 0.0
        if np.isnan(upper_bound):
            upper_bound = lower_bound
        if upper_bound < lower_bound:
            upper_bound = lower_bound

        numeric_bounds[column] = {
            "lower": max(0.0, lower_bound),
            "upper": max(lower_bound, upper_bound),
        }
        filled_numeric[column] = column_frame.clip(
            lower=numeric_bounds[column]["lower"],
            upper=numeric_bounds[column]["upper"],
        )

    engagement_score = filled_numeric["total_visits"] * filled_numeric["avg_page_views"]
    high_engagement_threshold = float(engagement_score.median()) if len(engagement_score) else 0.0

    return {
        "numeric_medians": numeric_medians,
        "numeric_bounds": numeric_bounds,
        "high_engagement_threshold": high_engagement_threshold,
    }


def transform_dataframe(dataframe: pd.DataFrame | list[dict[str, Any]], state: dict[str, Any]) -> PreparedFrames:
    frame = normalize_dataframe(dataframe)
    numeric_bounds = state.get("numeric_bounds", {})

    for column in RAW_NUMERIC_COLUMNS:
        numeric_series = _safe_to_numeric(frame[column]).fillna(state["numeric_medians"][column]).clip(lower=0)
        bounds = numeric_bounds.get(column)
        if bounds is not None:
            numeric_series = numeric_series.clip(lower=bounds["lower"], upper=bounds["upper"])
        frame[column] = numeric_series

    for column in CATEGORICAL_COLUMNS:
        frame[column] = frame[column].map(_normalize_category_value)

    frame[TEXT_COLUMN] = frame[TEXT_COLUMN].map(clean_text)
    text_tokens = frame[TEXT_COLUMN].map(_tokenize_text)

    frame["engagement_score"] = frame["total_visits"] * frame["avg_page_views"]
    frame["time_per_visit"] = frame["time_on_website_sec"] / (frame["total_visits"] + 1)
    frame["log_visits"] = np.log1p(frame["total_visits"])
    frame["log_time"] = np.log1p(frame["time_on_website_sec"])
    frame["log_pageviews"] = np.log1p(frame["avg_page_views"])
    frame["visits_x_time"] = frame["total_visits"] * frame["time_on_website_sec"]
    frame["high_engagement"] = frame["engagement_score"] > state["high_engagement_threshold"]
    frame["text_length"] = frame[TEXT_COLUMN].str.len()
    frame["word_count"] = text_tokens.map(len)
    frame["unique_words"] = text_tokens.map(lambda value: len(set(value)))
    frame["avg_word_length"] = text_tokens.map(
        lambda value: float(np.mean([len(word) for word in value])) if value else 0.0
    )
    frame["positive_word_count"] = text_tokens.map(lambda value: sum(word in POSITIVE_WORDS for word in value))
    frame["negative_word_count"] = text_tokens.map(lambda value: sum(word in NEGATIVE_WORDS for word in value))
    frame["sentiment_ratio"] = (frame["positive_word_count"] + 1) / (frame["negative_word_count"] + 1)

    cat_frame = frame[ALL_NUMERIC_COLUMNS + CATEGORICAL_COLUMNS + [TEXT_COLUMN]].copy()
    feature_store = frame[ENGINEERED_COLUMNS].copy()

    return PreparedFrames(
        feature_store=feature_store,
        cat_frame=cat_frame,
        transformed_source=frame,
    )
