from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IA_ML_ROOT = PROJECT_ROOT / "IA-ML_service"
DEFAULT_CSV = PROJECT_ROOT / "data" / "train.csv"


def load_env_file() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def configure_host_database_defaults() -> None:
    if os.environ.get("DB_HOST") == "db":
        os.environ["DB_HOST"] = "localhost"


def running_inside_container() -> bool:
    return Path("/.dockerenv").exists() or os.environ.get("RUNNING_IN_DOCKER") == "1"


def run_inside_ia_ml_container() -> bool:
    if running_inside_container() or os.environ.get("LEADS_ACTIVITY_FORCE_LOCAL") == "1":
        return False

    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "ia-ml",
        "python",
        "-c",
        (
            "from services.analyse_comportementale.import_service import initialize_from_csv; "
            "result = initialize_from_csv('/app/data/train.csv'); "
            "print('Initialisation Analyse Comportementale terminee:'); "
            "[print(f'- {key}: {value}') for key, value in result.items()]"
        ),
    ]
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return True


def main() -> None:
    load_env_file()
    if run_inside_ia_ml_container():
        return

    configure_host_database_defaults()
    sys.path.insert(0, str(IA_ML_ROOT))

    from services.analyse_comportementale.import_service import initialize_from_csv

    csv_path = Path(os.environ.get("LEADS_ACTIVITY_CSV", DEFAULT_CSV))
    result = initialize_from_csv(csv_path)
    print("Initialisation Analyse Comportementale terminee:")
    for key, value in result.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
