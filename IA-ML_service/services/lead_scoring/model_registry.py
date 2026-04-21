from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

from core.config import get_settings


def _artifacts_dir() -> Path:
    path = Path(get_settings().lead_scoring_artifacts_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def latest_artifact_path() -> Path:
    return _artifacts_dir() / "latest.pkl"


def versioned_artifact_path(model_version: str) -> Path:
    return _artifacts_dir() / f"{model_version}.pkl"


def save_artifact(artifact: dict[str, Any]) -> str:
    model_version = artifact["metadata"]["model_version"]
    version_path = versioned_artifact_path(model_version)
    latest_path = latest_artifact_path()

    with version_path.open("wb") as file_handle:
        pickle.dump(artifact, file_handle)

    with latest_path.open("wb") as file_handle:
        pickle.dump(artifact, file_handle)

    return str(version_path)


def load_latest_artifact() -> dict[str, Any] | None:
    path = latest_artifact_path()
    if not path.exists():
        return None

    with path.open("rb") as file_handle:
        return pickle.load(file_handle)
