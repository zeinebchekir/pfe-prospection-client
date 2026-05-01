import os
import traceback
from datetime import datetime

LOGS_DIR = "/opt/airflow/exports/etl_logs"
os.makedirs(LOGS_DIR, exist_ok=True)


def _log_path(dag_id: str, run_id: str) -> str:
    """Un fichier de log par DAG par jour — plusieurs runs dedans."""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOGS_DIR, f"{dag_id}__{today}.txt")

def log_task_start(dag_id: str, run_id: str, task_id: str):
    path = _log_path(dag_id, run_id)
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}]  ▶  DÉBUT      {task_id}\n"
    _append(path, line)


def log_task_success(dag_id: str, run_id: str, task_id: str,
                     duration_sec: float, details: dict = None):
    path = _log_path(dag_id, run_id)
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"[{now}]  ✓  SUCCÈS     {task_id}  ({duration_sec:.1f}s)\n"]
    if details:
        for k, v in details.items():
            lines.append(f"            → {k}: {v}\n")
    lines.append("\n")
    _append(path, "".join(lines))


def log_task_failure(dag_id: str, run_id: str, task_id: str,
                     duration_sec: float, exc: Exception):
    path = _log_path(dag_id, run_id)
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tb   = traceback.format_exc()
    lines = [
        f"[{now}]  ✗  ÉCHEC      {task_id}  ({duration_sec:.1f}s)\n",
        f"            Exception  : {type(exc).__name__}: {exc}\n",
        f"            Traceback  :\n",
    ]
    for tb_line in tb.splitlines():
        lines.append(f"              {tb_line}\n")
    lines.append("\n")
    _append(path, "".join(lines))

def log_dag_header(dag_id: str, run_id: str):
    path = _log_path(dag_id, run_id)
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = (
        f"\n{'─' * 70}\n"
        f"  RUN        : {run_id}\n"
        f"  Démarré le : {now}\n"
        f"{'─' * 70}\n\n"
    )
    _append(path, header)

def log_dag_footer(dag_id: str, run_id: str,
                   total_tasks: int, failed_tasks: list):
    """Écrit le résumé final à la fin du run."""
    path = _log_path(dag_id, run_id)
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if failed_tasks:
        status  = "ÉCHEC"
        details = f"  Tâches en échec : {', '.join(failed_tasks)}\n"
    else:
        status  = "SUCCÈS"
        details = ""

    footer = (
        f"\n{'=' * 70}\n"
        f"  Terminé le : {now}\n"
        f"  Statut     : {status}\n"
        f"  Total tâches : {total_tasks}\n"
        f"{details}"
        f"{'=' * 70}\n"
    )
    _append(path, footer)


def _append(path: str, content: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)