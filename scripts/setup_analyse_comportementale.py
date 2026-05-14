from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_CSV = PROJECT_ROOT / "data" / "train.csv"
REQUIRED_SERVICES = {"db", "web", "frontend", "ia-ml"}
EXTERNAL_NETWORK = "etl_service_default"


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(command)}")
    return subprocess.run(command, cwd=PROJECT_ROOT, check=check)


def capture(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def ensure_train_csv() -> None:
    if TRAIN_CSV.exists():
        return

    raise SystemExit(
        "Fichier manquant: data/train.csv\n"
        "Copie le dataset dans pfe-prospection-client/data/train.csv puis relance cette commande."
    )


def ensure_external_network() -> None:
    inspected = capture(["docker", "network", "inspect", EXTERNAL_NETWORK])
    if inspected.returncode == 0:
        return

    run(["docker", "network", "create", EXTERNAL_NETWORK])


def compose_up() -> None:
    run(["docker", "compose", "up", "-d", "--build"])


def wait_for_services(timeout_seconds: int = 180) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        listed = capture(["docker", "compose", "ps", "--services", "--status", "running"])
        running = {line.strip() for line in listed.stdout.splitlines() if line.strip()}
        missing = REQUIRED_SERVICES - running
        if not missing:
            return

        print(f"Attente des services: {', '.join(sorted(missing))}")
        time.sleep(5)

    run(["docker", "compose", "ps"], check=False)
    raise SystemExit("Les services Docker ne sont pas tous actifs apres attente.")


def initialize_data() -> None:
    run([sys.executable, "scripts/init_leads_activity.py"])


def restart_ui_services() -> None:
    run(["docker", "compose", "restart", "ia-ml", "frontend"], check=False)


def main() -> None:
    ensure_train_csv()
    ensure_external_network()
    compose_up()
    wait_for_services()
    initialize_data()
    restart_ui_services()

    print("\nAnalyse Comportementale prete.")
    print("Frontend : http://localhost:5174")
    print("API IA-ML : http://localhost:8002/docs")
    print("KPI : http://localhost:8002/analyse-comportementale/kpis")


if __name__ == "__main__":
    main()
