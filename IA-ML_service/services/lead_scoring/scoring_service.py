from __future__ import annotations

from uuid import UUID

import numpy as np
import pandas as pd

from core.config import get_settings

from .feature_engineering import ENGINEERED_COLUMNS, transform_dataframe
from .model_registry import load_latest_artifact
from .repository import load_opportunity_by_id, persist_scored_rows, utcnow


def _ensure_artifact() -> dict:
    artifact = load_latest_artifact()
    if artifact is not None:
        return artifact

    settings = get_settings()
    if not settings.lead_scoring_auto_train_on_missing:
        raise RuntimeError("Aucun modèle de scoring entraîné n'est disponible.")

    from .training_service import train_lead_scoring_model

    train_lead_scoring_model()
    artifact = load_latest_artifact()
    if artifact is None:
        raise RuntimeError("Le modèle n'a pas pu être créé automatiquement.")
    return artifact


def classify_temperature(probability: float) -> str:
    settings = get_settings()
    if probability >= settings.lead_scoring_hot_threshold:
        return "HOT"
    if probability >= settings.lead_scoring_warm_threshold:
        return "WARM"
    return "COLD"


def score_dataframe(dataframe: pd.DataFrame, artifact: dict | None = None) -> pd.DataFrame:
    current_artifact = artifact or _ensure_artifact()
    prepared = transform_dataframe(dataframe, current_artifact["preprocessing"])

    cat_model = current_artifact["models"]["catboost"]
    threshold = current_artifact["metadata"]["threshold"]
    model_version = current_artifact["metadata"]["model_version"]

    final_probability = cat_model.predict_proba(prepared.cat_frame)[:, 1]

    scored_frame = prepared.feature_store.copy()
    scored_frame["lead_id"] = prepared.transformed_source["lead_id"].astype(str)
    scored_frame["lead_score_probability"] = final_probability
    scored_frame["lead_score_predicted"] = np.rint(final_probability * 100).clip(0, 100).astype(int)
    scored_frame["lead_temperature"] = [classify_temperature(probability) for probability in final_probability]
    scored_frame["model_version"] = model_version
    scored_frame["scored_at"] = utcnow()
    scored_frame["predicted_label"] = (final_probability >= threshold).astype(int)

    return scored_frame


def rescore_lead_by_id(lead_id: UUID | str) -> dict:
    artifact = _ensure_artifact()
    dataframe = load_opportunity_by_id(lead_id)
    if dataframe.empty:
        raise ValueError(f"Lead introuvable pour lead_id={lead_id}")

    scored_frame = score_dataframe(dataframe, artifact)
    persist_scored_rows(scored_frame.drop(columns=["predicted_label"]))

    record = scored_frame.iloc[0].to_dict()
    feature_values = {column: record[column] for column in ENGINEERED_COLUMNS}

    return {
        "lead_id": record["lead_id"],
        "lead_score_probability": float(record["lead_score_probability"]),
        "lead_score_predicted": int(record["lead_score_predicted"]),
        "lead_temperature": record["lead_temperature"],
        "model_version": record["model_version"],
        "scored_at": record["scored_at"],
        "feature_values": feature_values,
    }
