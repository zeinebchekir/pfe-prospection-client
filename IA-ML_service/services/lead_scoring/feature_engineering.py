from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from core.config import get_settings


TARGET_COLUMN = "lead_score"
TEXT_COLUMN = "interaction_history"

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

INFLUENTIAL_COLUMNS = {
    "job_title",
    "industry",
    "company_size",
    "annual_revenue",
    "country",
    "city",
    "lead_source",
    "total_visits",
    "time_on_website_sec",
    "avg_page_views",
    "last_activity",
    "last_notable_activity",
    TEXT_COLUMN,
}

LEAK_PATTERN = re.compile(
    r"\b(signé|signe|refusé|refuse|devis|accepté|accepte|fructueux|contrat)\b",
    flags=re.IGNORECASE,
)

POSITIVE_WORDS = [
    "interesse",
    "intéressé",
    "rappeler",
    "demo",
    "réunion",
    "reunion",
    "positif",
    "suite",
    "projet",
]

NEGATIVE_WORDS = [
    "pas",
    "jamais",
    "non",
    "annule",
    "annulé",
    "reporte",
    "reporté",
    "indisponible",
]


@dataclass
class PreparedFrames:
    feature_store: pd.DataFrame
    gbm_frame: pd.DataFrame
    cat_frame: pd.DataFrame
    transformed_source: pd.DataFrame


def _import_text_stack():
    try:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError as exc:
        raise RuntimeError(
            "Les dépendances ML ne sont pas installées. "
            "Rebuild le service ia-ml après mise à jour des requirements."
        ) from exc

    return TfidfVectorizer, TruncatedSVD


def normalize_dataframe(data: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    dataframe = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    dataframe = dataframe.rename(columns={col: DISPLAY_TO_DB_COLUMNS.get(col, col) for col in dataframe.columns})

    for column in ALL_NUMERIC_COLUMNS + CATEGORICAL_COLUMNS + [TEXT_COLUMN, TARGET_COLUMN, "lead_id"]:
        if column not in dataframe.columns:
            dataframe[column] = np.nan

    return dataframe


def clean_text(value: Any) -> str:
    text = str(value or "pas historique").strip()
    text = LEAK_PATTERN.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or "pas historique"


def _safe_to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def build_preprocessing_state(dataframe: pd.DataFrame) -> dict[str, Any]:
    settings = get_settings()
    frame = normalize_dataframe(dataframe)

    numeric_frame = frame[RAW_NUMERIC_COLUMNS].apply(_safe_to_numeric)
    numeric_medians = {
        column: float(numeric_frame[column].median())
        if not np.isnan(numeric_frame[column].median())
        else 0.0
        for column in RAW_NUMERIC_COLUMNS
    }

    filled_numeric = numeric_frame.fillna(numeric_medians)
    cleaned_text = frame[TEXT_COLUMN].map(clean_text)
    engagement_score = filled_numeric["total_visits"] * filled_numeric["avg_page_views"]
    high_engagement_threshold = float(engagement_score.median()) if len(engagement_score) else 0.0

    category_encoders: dict[str, dict[str, int]] = {}
    for column in CATEGORICAL_COLUMNS:
        categories = (
            frame[column]
            .fillna("Missing")
            .astype(str)
            .str.strip()
            .replace("", "Missing")
            .sort_values()
            .unique()
            .tolist()
        )
        category_encoders[column] = {value: index for index, value in enumerate(categories)}

    vectorizer = None
    svd_model = None
    component_count = 0

    if settings.lead_scoring_text_components > 0:
        TfidfVectorizer, TruncatedSVD = _import_text_stack()
        vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
        )
        tfidf_matrix = vectorizer.fit_transform(cleaned_text)

        max_components = min(
            settings.lead_scoring_text_components,
            max(0, tfidf_matrix.shape[0] - 1),
            max(0, tfidf_matrix.shape[1] - 1),
        )

        if max_components >= 1:
            svd_model = TruncatedSVD(n_components=max_components, random_state=42)
            svd_model.fit(tfidf_matrix)
            component_count = max_components

    return {
        "numeric_medians": numeric_medians,
        "high_engagement_threshold": high_engagement_threshold,
        "category_encoders": category_encoders,
        "vectorizer": vectorizer,
        "svd_model": svd_model,
        "text_component_count": component_count,
        "text_component_columns": [f"txt_{index}" for index in range(component_count)],
        "feature_count": len(ALL_NUMERIC_COLUMNS) + len(CATEGORICAL_COLUMNS) + component_count,
    }


def _build_text_features(frame: pd.DataFrame, state: dict[str, Any]) -> tuple[pd.Series, pd.DataFrame]:
    cleaned_text = frame[TEXT_COLUMN].map(clean_text)
    vectorizer = state["vectorizer"]
    svd_model = state["svd_model"]
    component_columns = state["text_component_columns"]

    if svd_model is None or not component_columns:
        text_components = pd.DataFrame(index=frame.index)
    else:
        tfidf_matrix = vectorizer.transform(cleaned_text)
        dense_components = svd_model.transform(tfidf_matrix)
        text_components = pd.DataFrame(
            dense_components,
            columns=component_columns,
            index=frame.index,
        )

    return cleaned_text, text_components


def transform_dataframe(dataframe: pd.DataFrame | list[dict[str, Any]], state: dict[str, Any]) -> PreparedFrames:
    frame = normalize_dataframe(dataframe)

    for column in RAW_NUMERIC_COLUMNS:
        frame[column] = _safe_to_numeric(frame[column]).fillna(state["numeric_medians"][column])

    for column in CATEGORICAL_COLUMNS:
        frame[column] = (
            frame[column]
            .fillna("Missing")
            .astype(str)
            .str.strip()
            .replace("", "Missing")
        )

    cleaned_text, text_components = _build_text_features(frame, state)
    frame[TEXT_COLUMN] = cleaned_text

    frame["engagement_score"] = frame["total_visits"] * frame["avg_page_views"]
    frame["time_per_visit"] = frame["time_on_website_sec"] / (frame["total_visits"] + 1)
    frame["log_visits"] = np.log1p(frame["total_visits"])
    frame["log_time"] = np.log1p(frame["time_on_website_sec"])
    frame["log_pageviews"] = np.log1p(frame["avg_page_views"])
    frame["visits_x_time"] = frame["total_visits"] * frame["time_on_website_sec"]
    frame["high_engagement"] = frame["engagement_score"] > state["high_engagement_threshold"]
    frame["text_length"] = frame[TEXT_COLUMN].str.len()
    frame["word_count"] = frame[TEXT_COLUMN].map(lambda value: len(value.split()))
    frame["unique_words"] = frame[TEXT_COLUMN].map(lambda value: len(set(value.lower().split())))
    frame["avg_word_length"] = frame[TEXT_COLUMN].map(
        lambda value: float(np.mean([len(word) for word in value.split()])) if value.split() else 0.0
    )
    frame["positive_word_count"] = frame[TEXT_COLUMN].map(
        lambda value: sum(word in value.lower() for word in POSITIVE_WORDS)
    )
    frame["negative_word_count"] = frame[TEXT_COLUMN].map(
        lambda value: sum(word in value.lower() for word in NEGATIVE_WORDS)
    )
    frame["sentiment_ratio"] = (frame["positive_word_count"] + 1) / (frame["negative_word_count"] + 1)

    encoded_categories = {}
    for column in CATEGORICAL_COLUMNS:
        encoder = state["category_encoders"][column]
        encoded_categories[f"{column}_enc"] = frame[column].map(lambda value: encoder.get(value, -1))

    encoded_categories_frame = pd.DataFrame(encoded_categories, index=frame.index)

    gbm_frame = pd.concat(
        [
            frame[ALL_NUMERIC_COLUMNS].reset_index(drop=True),
            encoded_categories_frame.reset_index(drop=True),
            text_components.reset_index(drop=True),
        ],
        axis=1,
    )
    gbm_frame.index = frame.index

    cat_frame = frame[ALL_NUMERIC_COLUMNS + CATEGORICAL_COLUMNS + [TEXT_COLUMN]].copy()

    feature_store = frame[ENGINEERED_COLUMNS].copy()

    return PreparedFrames(
        feature_store=feature_store,
        gbm_frame=gbm_frame,
        cat_frame=cat_frame,
        transformed_source=frame,
    )
