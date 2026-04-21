from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from core.config import get_settings

from .feature_engineering import (
    CATEGORICAL_COLUMNS,
    TARGET_COLUMN,
    TEXT_COLUMN,
    build_preprocessing_state,
    transform_dataframe,
)
from .model_registry import load_latest_artifact, save_artifact
from .repository import (
    load_all_opportunities,
    load_latest_performance_record,
    persist_performance_record,
    persist_scored_rows,
)
from .scoring_service import score_dataframe


def _import_training_stack():
    try:
        import optuna

        optuna.logging.set_verbosity(optuna.logging.WARNING)

        from catboost import CatBoostClassifier
        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )
        from sklearn.model_selection import StratifiedKFold, train_test_split
    except ImportError as exc:
        raise RuntimeError(
            "Les dépendances ML sont manquantes. "
            "Rebuild le service ia-ml pour activer l'entraînement du lead scoring."
        ) from exc

    return {
        "optuna": optuna,
        "CatBoostClassifier": CatBoostClassifier,
        "StratifiedKFold": StratifiedKFold,
        "train_test_split": train_test_split,
        "accuracy_score": accuracy_score,
        "precision_score": precision_score,
        "recall_score": recall_score,
        "f1_score": f1_score,
        "roc_auc_score": roc_auc_score,
    }


def _cat_feature_indices(prepared) -> list[int]:
    return [prepared.cat_frame.columns.get_loc(column) for column in CATEGORICAL_COLUMNS]


def _text_feature_indices(prepared) -> list[int]:
    return [prepared.cat_frame.columns.get_loc(TEXT_COLUMN)]


def _build_catboost_params(trial=None) -> dict:
    params = {
        "iterations": 180,
        "learning_rate": 0.05,
        "depth": 6,
        "l2_leaf_reg": 4.0,
        "random_strength": 1.0,
        "bagging_temperature": 0.3,
        "loss_function": "Logloss",
        "eval_metric": "AUC",
        "auto_class_weights": "Balanced",
        "verbose": 0,
        "random_seed": 42,
        "allow_writing_files": False,
    }

    if trial is None:
        return params

    params.update(
        {
            "iterations": trial.suggest_int("iterations", 120, 220),
            "learning_rate": trial.suggest_float("learning_rate", 0.03, 0.10, log=True),
            "depth": trial.suggest_int("depth", 4, 7),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 8.0),
            "random_strength": trial.suggest_float("random_strength", 0.1, 2.0),
            "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 0.8),
        }
    )
    return params


def _fit_catboost(prepared, y_values: pd.Series, params: dict):
    CatBoostClassifier = _import_training_stack()["CatBoostClassifier"]
    model = CatBoostClassifier(
        **params,
        cat_features=_cat_feature_indices(prepared),
        text_features=_text_feature_indices(prepared),
    )
    model.fit(prepared.cat_frame, y_values)
    return model


def _run_optuna(prepared, y_values: pd.Series) -> dict:
    imports = _import_training_stack()
    optuna = imports["optuna"]
    StratifiedKFold = imports["StratifiedKFold"]
    roc_auc_score = imports["roc_auc_score"]
    settings = get_settings()

    fold_strategy = StratifiedKFold(
        n_splits=settings.lead_scoring_optuna_folds,
        shuffle=True,
        random_state=42,
    )

    source_frame = prepared.transformed_source.copy()

    def objective(trial):
        params = _build_catboost_params(trial)
        fold_scores = []

        for train_index, validation_index in fold_strategy.split(source_frame, y_values):
            fold_train_source = source_frame.iloc[train_index].copy()
            fold_validation_source = source_frame.iloc[validation_index].copy()
            fold_state = build_preprocessing_state(fold_train_source)
            fold_train = transform_dataframe(fold_train_source, fold_state)
            fold_validation = transform_dataframe(fold_validation_source, fold_state)

            y_fold_train = y_values.iloc[train_index]
            y_fold_validation = y_values.iloc[validation_index]

            model = _fit_catboost(fold_train, y_fold_train, params)
            fold_probability = model.predict_proba(fold_validation.cat_frame)[:, 1]
            fold_scores.append(roc_auc_score(y_fold_validation, fold_probability))

        return float(np.mean(fold_scores))

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=settings.lead_scoring_optuna_trials, show_progress_bar=False)

    return _build_catboost_params() | study.best_params


def _threshold_from_probabilities(probabilities: np.ndarray, y_true: pd.Series) -> float:
    accuracy_score = _import_training_stack()["accuracy_score"]

    thresholds = np.arange(0.30, 0.71, 0.01)
    best_threshold = 0.50
    best_accuracy = 0.0

    for threshold in thresholds:
        accuracy = accuracy_score(y_true, (probabilities >= threshold).astype(int))
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = float(threshold)

    return best_threshold


def _prepare_trainable_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    prepared = dataframe.copy()
    prepared[TARGET_COLUMN] = pd.to_numeric(prepared[TARGET_COLUMN], errors="coerce")
    prepared = prepared.dropna(subset=[TARGET_COLUMN]).copy()
    prepared[TARGET_COLUMN] = prepared[TARGET_COLUMN].astype(int)
    return prepared


def _top_feature_importances(model, limit: int = 10) -> list[dict[str, float | str]]:
    feature_names = list(getattr(model, "feature_names_", []) or [])
    if not feature_names:
        return []

    importances = model.get_feature_importance()
    rows = [
        {
            "feature": str(feature_name),
            "importance": float(importance),
        }
        for feature_name, importance in zip(feature_names, importances)
    ]
    rows.sort(key=lambda item: item["importance"], reverse=True)
    return rows[:limit]


def train_lead_scoring_model() -> dict:
    settings = get_settings()
    raw_dataframe = load_all_opportunities()
    trainable_dataframe = _prepare_trainable_dataframe(raw_dataframe)

    if len(trainable_dataframe) < settings.lead_scoring_min_train_rows:
        raise RuntimeError(
            f"Pas assez de lignes entraînables pour le lead scoring ({len(trainable_dataframe)})."
        )

    if trainable_dataframe[TARGET_COLUMN].nunique() < 2:
        raise RuntimeError("La colonne cible lead_score doit contenir au moins deux classes.")

    imports = _import_training_stack()
    train_test_split = imports["train_test_split"]
    accuracy_score = imports["accuracy_score"]
    precision_score = imports["precision_score"]
    recall_score = imports["recall_score"]
    f1_score = imports["f1_score"]
    roc_auc_score = imports["roc_auc_score"]

    dataframe_train, dataframe_test = train_test_split(
        trainable_dataframe,
        test_size=0.2,
        random_state=42,
        stratify=trainable_dataframe[TARGET_COLUMN],
    )
    dataframe_train = dataframe_train.copy()
    dataframe_test = dataframe_test.copy()

    y_train = dataframe_train[TARGET_COLUMN].astype(int)
    y_test = dataframe_test[TARGET_COLUMN].astype(int)

    preprocessing_state = build_preprocessing_state(dataframe_train)
    prepared_train = transform_dataframe(dataframe_train, preprocessing_state)
    prepared_test = transform_dataframe(dataframe_test, preprocessing_state)

    best_params = _run_optuna(prepared_train, y_train)
    evaluation_model = _fit_catboost(prepared_train, y_train, best_params)

    train_probability = evaluation_model.predict_proba(prepared_train.cat_frame)[:, 1]
    test_probability = evaluation_model.predict_proba(prepared_test.cat_frame)[:, 1]
    threshold = _threshold_from_probabilities(train_probability, y_train)
    test_prediction = (test_probability >= threshold).astype(int)

    full_preprocessing_state = build_preprocessing_state(trainable_dataframe)
    prepared_full = transform_dataframe(trainable_dataframe, full_preprocessing_state)
    final_model = _fit_catboost(
        prepared_full,
        trainable_dataframe[TARGET_COLUMN].astype(int),
        best_params,
    )
    top_importances = _top_feature_importances(final_model)

    last_training_date = datetime.now(timezone.utc)
    model_version = f"{settings.lead_scoring_model_name}-{last_training_date.strftime('%Y%m%d%H%M%S')}"

    feature_count = int(prepared_full.cat_frame.shape[1])
    artifact = {
        "metadata": {
            "model_name": settings.lead_scoring_model_name,
            "model_version": model_version,
            "threshold": float(threshold),
            "best_model": "catboost",
            "stack_name": "CatBoost",
            "feature_count": feature_count,
            "last_training_date": last_training_date,
            "optuna_trials": settings.lead_scoring_optuna_trials,
            "top_importances": top_importances,
        },
        "preprocessing": full_preprocessing_state,
        "models": {
            "catboost": final_model,
        },
    }
    save_artifact(artifact)

    performance_record = {
        "model_name": settings.lead_scoring_model_name,
        "model_version": model_version,
        "best_model": "catboost",
        "stack_name": f"CatBoost (Optuna x{settings.lead_scoring_optuna_trials})",
        "accuracy": float(accuracy_score(y_test, test_prediction)),
        "precision": float(precision_score(y_test, test_prediction, zero_division=0)),
        "recall": float(recall_score(y_test, test_prediction, zero_division=0)),
        "f1_score": float(f1_score(y_test, test_prediction, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, test_probability)),
        "threshold": float(threshold),
        "training_dataset_size": int(len(trainable_dataframe)),
        "feature_count": feature_count,
        "last_training_date": last_training_date,
        "top_importances": top_importances,
    }
    persist_performance_record(performance_record)

    rescored_rows = persist_scored_rows(score_dataframe(raw_dataframe, artifact).drop(columns=["predicted_label"]))

    return {
        **performance_record,
        "status": "success",
        "rescored_rows": rescored_rows,
    }


def latest_performance_or_none() -> dict | None:
    performance = load_latest_performance_record()
    if performance is None:
        return None

    artifact = load_latest_artifact()
    if artifact is None:
        performance["top_importances"] = []
        return performance

    artifact_metadata = artifact.get("metadata", {})
    if artifact_metadata.get("model_version") != performance.get("model_version"):
        performance["top_importances"] = []
        return performance

    performance["top_importances"] = artifact_metadata.get("top_importances") or _top_feature_importances(
        artifact["models"]["catboost"]
    )
    return performance
