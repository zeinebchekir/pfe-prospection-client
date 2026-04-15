"""
dag_rapport_pdf.py
DAG Airflow dédié à la génération automatique du rapport PDF journalier.
Schedule : tous les jours à 23:55.
"""

import requests
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────

FASTAPI_BASE = "http://fastapi:8000"   # adapter selon ton docker-compose
TIMEOUT      = 120                 # secondes


# ─────────────────────────────────────────────
#  TASKS
# ─────────────────────────────────────────────

def generate_rapport_pdf(**context):
    """
    Appelle l'endpoint FastAPI pour générer et sauvegarder le rapport PDF.
    La date utilisée est celle du jour logique du DAG run.
    """
    logical_date = context["logical_date"]
    day          = logical_date.strftime("%Y-%m-%d")

    print(f"[RAPPORT PDF] Génération du rapport pour le {day}")

    url = f"{FASTAPI_BASE}/api/rapport/pdf/generate/{day}"
    print(url)
    try:
        resp = requests.post(url, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        print(f"[RAPPORT PDF] ✓ Rapport généré")
        print(f"  → Date        : {data.get('report_date')}")
        print(f"  → Taille      : {data.get('file_size_kb')} KB")
        print(f"  → Runs        : {data.get('nb_runs')}")
        print(f"  → Alertes     : {data.get('nb_alertes')}")
        print(f"  → Taux succès : {data.get('success_rate')}%")

        context["ti"].xcom_push(key="report_date",   value=day)
        context["ti"].xcom_push(key="file_size_kb",  value=data.get("file_size_kb"))
        context["ti"].xcom_push(key="success_rate",  value=data.get("success_rate"))

        return data

    except requests.HTTPError as e:
        print(f"[RAPPORT PDF] ✗ Erreur HTTP {resp.status_code}: {resp.text}")
        raise
    except Exception as e:
        print(f"[RAPPORT PDF] ✗ Erreur: {e}")
        raise


def verify_rapport_saved(**context):
    """Vérifie que le rapport a bien été sauvegardé en base."""
    ti  = context["ti"]
    day = ti.xcom_pull(task_ids="generate_rapport_pdf", key="report_date")

    url = f"{FASTAPI_BASE}/api/rapport/pdf/list"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        rapports = resp.json()

        found = any(r.get("report_date") == day for r in rapports)
        if not found:
            raise ValueError(f"Rapport {day} introuvable en base après génération")

        size_kb = ti.xcom_pull(task_ids="generate_rapport_pdf", key="file_size_kb")
        print(f"[VERIFY] ✓ Rapport {day} confirmé en base ({size_kb} KB)")

    except Exception as e:
        print(f"[VERIFY] ✗ {e}")
        raise


# ─────────────────────────────────────────────
#  DAG
# ─────────────────────────────────────────────

default_args = {
    "owner":            "numeryx",
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="rapport_pdf_journalier",
    description="Génération automatique du rapport ETL PDF — 23h55 chaque jour",
    start_date=datetime(2026, 4, 1),
    schedule="55 23 * * *",          # tous les jours à 23:55
    catchup=False,
    default_args=default_args,
    tags=["rapport", "pdf", "journalier"],
    max_active_runs=1,
) as dag:

    t_generate = PythonOperator(
        task_id="generate_rapport_pdf",
        python_callable=generate_rapport_pdf,
    )

    t_verify = PythonOperator(
        task_id="verify_rapport_saved",
        python_callable=verify_rapport_saved,
    )

    t_generate >> t_verify