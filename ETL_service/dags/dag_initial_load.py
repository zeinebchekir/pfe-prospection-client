from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys, json, os

sys.path.insert(0, "/opt/airflow/ETL_pipeline")

from scrapers.boamp import BoampService
from scrapers.dataGouv import DataGouvService
from scrapers.sirene import SireneService
from extractors.Boamp.data_extraction import get_global_information
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv
from exports.excel_exporter import export_to_excel
from db.database import SessionLocal
from db import sync_crud

# ──────────────────────────────────────────────
#  Chemins fixes
# ──────────────────────────────────────────────
RAW_BOAMP_PATH    = "/tmp/raw_boamp.json"
RAW_DATAGOUV_PATH = "/tmp/raw_datagouv.json"
EXPORT_DIR        = "/opt/airflow/exports"

def _write(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _delete(path):
    if os.path.exists(path):
        os.remove(path)

def _get_last_sync(source: str) -> str:
    """Retourne la date de dernière sync formatée en string."""
    db = SessionLocal()
    try:
        return sync_crud.get_last_sync_date(db, source)
    finally:
        db.close()

def _update_sync(source: str, date: str,total_clean: int):
    """Met à jour la date de sync en base."""
    with SessionLocal() as db:
        sync_crud.update_sync_state(db, source, date,total_clean)

# ──────────────────────────────────────────────
#  SCRAPING
# ──────────────────────────────────────────────

def scrape_boamp(is_incremental: bool = False, **context):
    aujourdhui     = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    codes          = ["186", "14", "453", "463", "454", "163"]
    codes_fmt      = ",".join([f'"{c}"' for c in codes])

    if is_incremental:
        last_sync = _get_last_sync("BOAMP")
        filtre    = (
            f'descripteur_code IN ({codes_fmt})'
            f' AND datelimitereponse >= "{aujourdhui}"'
            f' AND dateparution >= "{last_sync}"'
        )
        print(f"[SCRAPE BOAMP DELTA] depuis {last_sync}")
    else:
        filtre = (
            f'descripteur_code IN ({codes_fmt})'
            f' AND datelimitereponse >= "{aujourdhui}"'
        )
        print("[SCRAPE BOAMP INITIAL]")

    raw = BoampService().source_scraping(filtre=filtre)
    _write(RAW_BOAMP_PATH, raw)

    context["ti"].xcom_push(key="total_raw",        value=len(raw))
    context["ti"].xcom_push(key="watermark_start",  value=aujourdhui)
    print(f"[SCRAPE BOAMP] {len(raw)} avis")


def scrape_datagouv( **context):
    aujourdhui = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    # Lit le filtre depuis conf si pas passé directement
    conf   = context.get("dag_run").conf or {}
    filtre = conf.get("query", None)

    # Construit le filtre selon la situation
    if not filtre:
        # Filtre par défaut — scraping régulier
        filtres = [{
            "etat_administratif" : "A",
            "activite_principale": ["62.01Z", "62.02A", "62.02B", "63.11Z"]
        }]
    else:
        # Filtre de recherche — SIREN ou nom passé par l'API
        filtres = [{"q": filtre}]

    raw = DataGouvService().source_scraping(filtre=filtres)
    _write(RAW_DATAGOUV_PATH, raw)

    context["ti"].xcom_push(key="total_raw",       value=len(raw))
    if not filtre:
        context["ti"].xcom_push(key="watermark_start", value=aujourdhui)
    print(f"[SCRAPE DATAGOUV] {len(raw)} entreprises")


def scrape_sirene(**context):
    aujourdhui = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    last_sync  = _get_last_sync("datagouv")
    #last_sync="2026-03-29T13:00:00"
    token = os.environ.get("INSEE_TOKEN", "")
    if not token:
        raise ValueError("INSEE_TOKEN manquant dans les variables d'environnement")
    raw  = SireneService(token=token).source_scraping(last_sync)
    _write(RAW_DATAGOUV_PATH, raw)

    context["ti"].xcom_push(key="total_raw",       value=len(raw))
    context["ti"].xcom_push(key="watermark_start", value=aujourdhui)
    print(f"[SCRAPE SIRENE] {len(raw)} entrées depuis {last_sync}")


# ──────────────────────────────────────────────
#  EXTRACTION
# ──────────────────────────────────────────────

def extract_boamp(**context):
    raw   = _read(RAW_BOAMP_PATH)
    clean = get_global_information(raw)
    _write(RAW_BOAMP_PATH, clean)   # écrase avec les données propres
    context["ti"].xcom_push(key="total_clean", value=len(clean))
    print(f"[EXTRACT BOAMP] {len(clean)} entreprises extraites")


def extract_datagouv(**context):
    raw   = _read(RAW_DATAGOUV_PATH)
    clean = extract_data_from_datagouv(raw)
    _write(RAW_DATAGOUV_PATH, clean)
    context["ti"].xcom_push(key="total_clean", value=len(clean))
    print(f"[EXTRACT DATAGOUV] {len(clean)} entreprises extraites")


# ──────────────────────────────────────────────
#  EXPORT
# ──────────────────────────────────────────────

def export_boamp(**context):
    clean = _read(RAW_BOAMP_PATH)
    path  = export_to_excel(clean, f"{EXPORT_DIR}/prospects_BOAMP.xlsx")
    context["ti"].xcom_push(key="fichier", value=path)
    print(f"[EXPORT BOAMP] {path}")


def export_datagouv(**context):
    clean = _read(RAW_DATAGOUV_PATH)
    path  = export_to_excel(clean, f"{EXPORT_DIR}/prospects_DATAGOUV.xlsx")
    context["ti"].xcom_push(key="fichier", value=path)
    print(f"[EXPORT DATAGOUV] {path}")


# ──────────────────────────────────────────────
#  CLEANUP
# ──────────────────────────────────────────────

def cleanup(**context):
    _delete(RAW_BOAMP_PATH)
    _delete(RAW_DATAGOUV_PATH)
    print("[CLEANUP] fichiers temporaires supprimés")


# ──────────────────────────────────────────────
#  RAPPORT FINAL
# ──────────────────────────────────────────────

def rapport_final(sources: list, **context):
    ti = context["ti"]
    print("=" * 50)
    print(f"[RAPPORT] Run : {context['run_id']}")

    for s in sources:
        # Gère les deux formats : string simple ou dict avec task_ids explicites
        if isinstance(s, dict):
            source      = s["source"]
            task_scrape = s["task_scrape"]
            task_ext    = s["task_ext"]
            task_exp    = s["task_exp"]
        else:
            source      = s
            task_scrape = f"scrape_{s.lower()}"
            task_ext    = f"extract_{s.lower()}"
            task_exp    = f"export_{s.lower()}"

        total_raw   = ti.xcom_pull(task_ids=task_scrape, key="total_raw")
        total_clean = ti.xcom_pull(task_ids=task_ext,    key="total_clean")
        fichier     = ti.xcom_pull(task_ids=task_exp,    key="fichier")
        watermark   = ti.xcom_pull(task_ids=task_scrape, key="watermark_start")

        print(f"  {source} — bruts: {total_raw} | extraits: {total_clean} | fichier: {fichier}")

        if watermark:
            _update_sync(source, watermark, total_clean if total_clean else 0)

    print("=" * 50)


# ──────────────────────────────────────────────
#  DAG 1 — Chargement initial
# ──────────────────────────────────────────────

with DAG(
    dag_id="initial_load",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["initial", "scraping"],
) as dag1:

    t_scrape_b = PythonOperator(task_id="scrape_boamp",     python_callable=scrape_boamp,    op_kwargs={"is_incremental": False})
    t_scrape_d = PythonOperator(task_id="scrape_datagouv",  python_callable=scrape_datagouv)
    t_ext_b    = PythonOperator(task_id="extract_boamp",    python_callable=extract_boamp)
    t_ext_d    = PythonOperator(task_id="extract_datagouv", python_callable=extract_datagouv)
    t_export_b = PythonOperator(task_id="export_boamp",     python_callable=export_boamp)
    t_export_d = PythonOperator(task_id="export_datagouv",  python_callable=export_datagouv)
    t_rapport  = PythonOperator(task_id="rapport_final",    python_callable=rapport_final,   op_kwargs={"sources": ["boamp", "datagouv"]})
    t_cleanup  = PythonOperator(task_id="cleanup",          python_callable=cleanup)

    t_scrape_b >> t_ext_b >> t_export_b
    t_scrape_d >> t_ext_d >> t_export_d
    [t_export_b, t_export_d
    ] >> t_rapport >> t_cleanup


# ──────────────────────────────────────────────
#  DAG 2 — Sync delta DataGouv / Sirene
# ──────────────────────────────────────────────

with DAG(
    dag_id="sync_datagouv",           # ← nom corrigé
    start_date=datetime(2026, 3, 27),  # ← date ajoutée
    schedule="0 */6 * * *",
    catchup=False,
    tags=["delta", "scraping"],
) as dag2:

    t_scrape = PythonOperator(task_id="scrape_sirene",    python_callable=scrape_sirene)
    t_ext    = PythonOperator(task_id="extract_datagouv", python_callable=extract_datagouv)
    t_export = PythonOperator(task_id="export_datagouv",  python_callable=export_datagouv)
    t_rapport= PythonOperator(task_id="rapport_final",    python_callable=rapport_final,  op_kwargs={
            "sources": [
                {
                    "source"     : "datagouv",
                    "task_scrape": "scrape_sirene",    # ← vrai nom task
                    "task_ext"   : "extract_datagouv",
                    "task_exp"   : "export_datagouv",
                }
            ]
        })
    t_cleanup= PythonOperator(task_id="cleanup",          python_callable=cleanup)

    t_scrape >> t_ext >> t_export >> t_rapport >> t_cleanup


# ──────────────────────────────────────────────
#  DAG 3 — Sync delta BOAMP
# ──────────────────────────────────────────────

with DAG(
    dag_id="sync_boamp",              # ← nom corrigé
    start_date=datetime(2026, 3, 27),  # ← date ajoutée
    schedule="0 6 * * *",
    catchup=False,
    tags=["delta", "scraping"],
) as dag3:

    t_scrape = PythonOperator(task_id="scrape_boamp",  python_callable=scrape_boamp, op_kwargs={"is_incremental": True})
    t_ext    = PythonOperator(task_id="extract_boamp", python_callable=extract_boamp)
    t_export = PythonOperator(task_id="export_boamp",  python_callable=export_boamp)
    t_rapport= PythonOperator(task_id="rapport_final", python_callable=rapport_final, op_kwargs={"sources": ["boamp"]})
    t_cleanup= PythonOperator(task_id="cleanup",       python_callable=cleanup)

    t_scrape >> t_ext >> t_export >> t_rapport >> t_cleanup


with DAG(
    dag_id="search_new_lead",
    start_date=datetime(2026, 3, 27),
    schedule=None,
    catchup=False,
    tags=["delta", "scraping"],
) as dag4:
    t_scrape = PythonOperator(task_id="scrape_datagouv",    python_callable=scrape_datagouv)
    t_ext    = PythonOperator(task_id="extract_datagouv", python_callable=extract_datagouv)
    t_export = PythonOperator(task_id="export_datagouv",  python_callable=export_datagouv)
    t_rapport= PythonOperator(task_id="rapport_final",    python_callable=rapport_final,  op_kwargs={
        "sources": [
            {
                "source"     : "datagouv",
                "task_scrape": "scrape_datagouv",    # ← vrai nom task
                "task_ext"   : "extract_datagouv",
                "task_exp"   : "export_datagouv",
            }
        ]
        })
    t_cleanup= PythonOperator(task_id="cleanup",          python_callable=cleanup)

    t_scrape >> t_ext >> t_export >> t_rapport >> t_cleanup