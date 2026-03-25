from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys, json, os
sys.path.insert(0, "/opt/airflow/ETL_pipeline")

from scrapers.boamp import BoampService
from scrapers.dataGouv import DataGouvService
from extractors.Boamp.data_extraction import get_global_information
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv
from exports.excel_exporter import export_to_excel
# from db.database import SessionLocal
# from db import crud

# ──────────────────────────────────────────────
#  Chemins fixes — écrasés à chaque run
# ──────────────────────────────────────────────

RAW_BOAMP_PATH    = "/tmp/raw_boamp.json"
RAW_DATAGOUV_PATH = "/tmp/raw_datagouv.json"


def _write(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def _read(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _delete(path: str):
    if os.path.exists(path):
        os.remove(path)


# ──────────────────────────────────────────────
#  ÉTAPE 1 — Scraping
# ──────────────────────────────────────────────

def scrape_boamp(**context):
    codes         = ["186", "14", "453", "463", "454", "163"]
    codes_fmt     = ",".join([f'"{c}"' for c in codes])
    aujourdhui    = datetime.now().strftime("%Y-%m-%d")
    filtre        = f'descripteur_code IN ({codes_fmt}) AND datelimitereponse >= "{aujourdhui}"'

    raw = BoampService().source_scraping(filtre=filtre)

    # Écrase l'ancien fichier
    _write(RAW_BOAMP_PATH, raw)

    print(f"[SCRAPE BOAMP] {len(raw)} avis → {RAW_BOAMP_PATH}")
    context["ti"].xcom_push(key="total_raw", value=len(raw))


def scrape_datagouv(**context):
    raw = DataGouvService().source_scraping()

    # Écrase l'ancien fichier
    _write(RAW_DATAGOUV_PATH, raw)

    print(f"[SCRAPE DATAGOUV] {len(raw)} entreprises → {RAW_DATAGOUV_PATH}")
    context["ti"].xcom_push(key="total_raw", value=len(raw))


# ──────────────────────────────────────────────
#  ÉTAPE 2 — Extraction
# ──────────────────────────────────────────────

def extract_boamp(**context):
    raw   = _read(RAW_BOAMP_PATH)
    clean = get_global_information(raw)

    context["ti"].xcom_push(key="total_clean", value=len(clean))
    print(f"[EXTRACT BOAMP] {len(clean)} entreprises extraites")


def extract_datagouv(**context):
    raw   = _read(RAW_DATAGOUV_PATH)
    clean = extract_data_from_datagouv(raw)

    context["ti"].xcom_push(key="total_clean", value=len(clean))
    print(f"[EXTRACT DATAGOUV] {len(clean)} entreprises extraites")


# ──────────────────────────────────────────────
#  ÉTAPE 3 — Export xlsx
# ──────────────────────────────────────────────

def export_boamp(**context):
    raw   = _read(RAW_BOAMP_PATH)
    clean = get_global_information(raw)
    path  = export_to_excel(clean, "prospects_BOAMP_initial.xlsx")

    context["ti"].xcom_push(key="fichier", value=path)
    print(f"[EXPORT BOAMP] {path}")


def export_datagouv(**context):
    raw   = _read(RAW_DATAGOUV_PATH)
    clean = extract_data_from_datagouv(raw)
    path  = export_to_excel(clean, "prospects_DATAGOUV_initial.xlsx")

    context["ti"].xcom_push(key="fichier", value=path)
    print(f"[EXPORT DATAGOUV] {path}")


# ──────────────────────────────────────────────
#  ÉTAPE 4 — Nettoyage fichiers temporaires
# ──────────────────────────────────────────────

def cleanup(**context):
    _delete(RAW_BOAMP_PATH)
    _delete(RAW_DATAGOUV_PATH)
    print(f"[CLEANUP] fichiers temporaires supprimés")


# ──────────────────────────────────────────────
#  ÉTAPE 5 — Rapport final
# ──────────────────────────────────────────────

def rapport_final(**context):
    ti = context["ti"]

    raw_b   = ti.xcom_pull(task_ids="scrape_boamp",    key="total_raw")
    raw_d   = ti.xcom_pull(task_ids="scrape_datagouv", key="total_raw")
    clean_b = ti.xcom_pull(task_ids="extract_boamp",   key="total_clean")
    clean_d = ti.xcom_pull(task_ids="extract_datagouv",key="total_clean")
    fich_b  = ti.xcom_pull(task_ids="export_boamp",    key="fichier")
    fich_d  = ti.xcom_pull(task_ids="export_datagouv", key="fichier")

    print("=" * 50)
    print(f"[RAPPORT] Run : {context['run_id']}")
    print(f"  BOAMP    — bruts: {raw_b} | extraits: {clean_b} | fichier: {fich_b}")
    print(f"  DATAGOUV — bruts: {raw_d} | extraits: {clean_d} | fichier: {fich_d}")
    print("=" * 50)

    # with SessionLocal() as db:
    #     crud.sauvegarder_sync(db, "BOAMP",    clean_b)
    #     crud.sauvegarder_sync(db, "DATAGOUV", clean_d)


# ──────────────────────────────────────────────
#  DAG
# ──────────────────────────────────────────────

with DAG(
    dag_id="initial_load",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["initial", "scraping"],
) as dag:

    t_scrape_b  = PythonOperator(task_id="scrape_boamp",     python_callable=scrape_boamp)
    t_scrape_d  = PythonOperator(task_id="scrape_datagouv",  python_callable=scrape_datagouv)
    t_ext_b     = PythonOperator(task_id="extract_boamp",    python_callable=extract_boamp)
    t_ext_d     = PythonOperator(task_id="extract_datagouv", python_callable=extract_datagouv)
    t_export_b  = PythonOperator(task_id="export_boamp",     python_callable=export_boamp)
    t_export_d  = PythonOperator(task_id="export_datagouv",  python_callable=export_datagouv)
    t_rapport   = PythonOperator(task_id="rapport_final",    python_callable=rapport_final)
    t_cleanup   = PythonOperator(task_id="cleanup",          python_callable=cleanup)

    # Pipeline parallèle — cleanup et rapport attendent les deux branches
    t_scrape_b  >> t_ext_b  >> t_export_b
    t_scrape_d  >> t_ext_d  >> t_export_d
    [t_export_b, t_export_d] >> t_rapport >> t_cleanup


