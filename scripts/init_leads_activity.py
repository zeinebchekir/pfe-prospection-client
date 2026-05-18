from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IA_ML_ROOT = PROJECT_ROOT / "IA-ML_service"
DEFAULT_CSV = PROJECT_ROOT / "data" / "train.csv"
LEGACY_DJANGO_TABLES = (
    "lead_opportunity",
    "leads_activity",
    "lead_sessions_raw",
    "lead_behavior_features",
    "lead_scores",
    "lead_notifications",
)


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


def cleanup_legacy_django_tables() -> None:
    if running_inside_container() or os.environ.get("LEADS_ACTIVITY_SKIP_DJANGO_CLEANUP") == "1":
        return

    db_user = os.environ.get("DB_USER", "crmpfe_user")
    db_name = os.environ.get("DB_NAME", "crmpfe_db")
    quoted_tables = ", ".join(f"'{table}'" for table in LEGACY_DJANGO_TABLES)
    qualified_tables = ", ".join(f"public.{table}" for table in LEGACY_DJANGO_TABLES)

    list_command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "db",
        "psql",
        "-U",
        db_user,
        "-d",
        db_name,
        "-v",
        "ON_ERROR_STOP=1",
        "-At",
        "-c",
        (
            "SELECT tablename FROM pg_tables "
            f"WHERE schemaname = 'public' AND tablename IN ({quoted_tables}) "
            "ORDER BY tablename;"
        ),
    ]
    listed = subprocess.run(
        list_command,
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if listed.returncode != 0:
        print("Impossible de verifier les anciennes tables Django DB:")
        print(listed.stdout.strip())
        raise SystemExit(listed.returncode)

    existing_tables = [line.strip() for line in listed.stdout.splitlines() if line.strip()]
    if not existing_tables:
        print("Django DB: aucune ancienne table Analyse Comportementale a supprimer.")
        return

    print("Django DB: suppression des anciennes tables Analyse Comportementale:")
    for table in existing_tables:
        print(f"- {table}")

    drop_command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "db",
        "psql",
        "-U",
        db_user,
        "-d",
        db_name,
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        f"DROP TABLE IF EXISTS {qualified_tables} CASCADE;",
    ]
    completed = subprocess.run(drop_command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


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
    cleanup_legacy_django_tables()
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
