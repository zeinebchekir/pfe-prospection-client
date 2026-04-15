from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psutil
import sys, json, os

# ── Fix: path must match the actual folder name on disk ──
sys.path.insert(0, "/opt/airflow/ETL_pipeline")
sys.path.insert(0, "/opt/airflow/ETL_pipeline/cleaners")

from scrapers.boamp import BoampService
from scrapers.dataGouv import DataGouvService
from scrapers.sirene import SireneService
from extractors.Boamp.data_extraction import get_global_information
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv
from extractors.dataGouv.boamp_enricher import enrich_boamp_data
from db.database import SessionLocal, create_tables
from db import sync_crud
from db import crud

from cleaners.boamp_cleaner import BoampCleaner
from cleaners.dataGouv_cleaner import DataGouvCleaner

# ──────────────────────────────────────────────
#  Chemins temporaires (supprimés après load)
# ──────────────────────────────────────────────
SHARED_DIR        = "/opt/airflow/shared_tmp"
RAW_BOAMP_PATH    = os.path.join(SHARED_DIR, "raw_boamp.json")
RAW_DATAGOUV_PATH = os.path.join(SHARED_DIR, "raw_datagouv.json")

os.makedirs(SHARED_DIR, exist_ok=True)

def _write(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _delete(path):
    if os.path.exists(path):
        os.remove(path)


def _get_last_sync(source: str):
    db = SessionLocal()
    try:
        return sync_crud.get_last_sync_date(db, source)
    finally:
        db.close()


def _update_sync(source: str, date: str, total_clean: int):
    with SessionLocal() as db:
        sync_crud.update_sync_state(db, source, date, total_clean)

def measure_task(func):
    """Décorateur qui mesure CPU/RAM d'une task et pousse via XCom."""
    def wrapper(**context):
        process = psutil.Process(os.getpid())

        # Snapshot avant
        cpu_before = process.cpu_percent(interval=0.1)
        ram_before = process.memory_info().rss / (1024 ** 2)  # MB

        # Exécuter la vraie task
        result = func(**context)

        # Snapshot après
        cpu_after = process.cpu_percent(interval=0.1)
        ram_after = process.memory_info().rss / (1024 ** 2)

        # Pousser les métriques via XCom
        context['ti'].xcom_push(key='cpu_used', value=round(cpu_after, 1))
        context['ti'].xcom_push(key='ram_used_mb', value=round(ram_after, 1))
        context['ti'].xcom_push(key='ram_delta_mb', value=round(ram_after - ram_before, 1))

        return result
    return wrapper

# ──────────────────────────────────────────────
#  DB INIT
# ──────────────────────────────────────────────

def init_db(**context):
    """Creates all tables (idempotent — CREATE TABLE IF NOT EXISTS)."""
    create_tables()
    print("[INIT DB] Tables created (or already exist).")


# ──────────────────────────────────────────────
#  SCRAPING
# ──────────────────────────────────────────────
@measure_task
def scrape_boamp(is_incremental: bool = False, **context):
    aujourdhui = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    codes      = ["186", "14", "453", "463", "454", "163"]
    codes_fmt  = ",".join([f'"{c}"' for c in codes])

    if is_incremental:
        last_sync = _get_last_sync("boamp")
        filtre = (
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
    for item in raw:
        item["date_scraping"] = aujourdhui
    _write(RAW_BOAMP_PATH, raw)
    
    context["ti"].xcom_push(key="total_raw",       value=len(raw))
    context["ti"].xcom_push(key="watermark_start", value=aujourdhui)
    print(f"[SCRAPE BOAMP] {len(raw)} avis bruts")

@measure_task
def scrape_datagouv(**context):
    aujourdhui = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    conf       = context.get("dag_run").conf or {}
    filtre     = conf.get("query", None)

    filtres = [{"q": filtre}] if filtre else [{"etat_administratif": "A"}]

    raw = DataGouvService().source_scraping(filtre=filtres)
    for item in raw:
        item["date_scraping"] = aujourdhui
    _write(RAW_DATAGOUV_PATH, raw)

    context["ti"].xcom_push(key="total_raw",       value=len(raw))
    context["ti"].xcom_push(key="watermark_start", value=aujourdhui)
    print(f"[SCRAPE DATAGOUV] {len(raw)} entreprises brutes")

@measure_task
def scrape_sirene(**context):
    aujourdhui = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    last_sync  = _get_last_sync("datagouv")

    token = os.environ.get("INSEE_TOKEN", "")
    if not token:
        raise ValueError("INSEE_TOKEN manquant dans les variables d'environnement")

    raw = SireneService(token=token).source_scraping(last_sync)
    for item in raw:
        item["date_scraping"] = aujourdhui
    _write(RAW_DATAGOUV_PATH, raw)

    context["ti"].xcom_push(key="total_raw",       value=len(raw))
    context["ti"].xcom_push(key="watermark_start", value=aujourdhui)
    print(f"[SCRAPE SIRENE] {len(raw)} entrées depuis {last_sync}")


# ──────────────────────────────────────────────
#  EXTRACTION
# ──────────────────────────────────────────────
@measure_task
def extract_boamp(**context):
    raw   = _read(RAW_BOAMP_PATH)
    clean = get_global_information(raw)
    _write(RAW_BOAMP_PATH, clean)
    context["ti"].xcom_push(key="total_extracted", value=len(clean))
    print(f"[EXTRACT BOAMP] {len(clean)} enregistrements extraits")

@measure_task
def enrich_boamp(**context):
    records = _read(RAW_BOAMP_PATH)
    enriched = enrich_boamp_data(records)
    _write(RAW_BOAMP_PATH, enriched)
    print(f"[ENRICH BOAMP] {len(enriched)} enregistrements enrichis avec DataGouv")

@measure_task
def extract_datagouv(**context):
    raw   = _read(RAW_DATAGOUV_PATH)
    clean = extract_data_from_datagouv(raw)
    _write(RAW_DATAGOUV_PATH, clean)
    context["ti"].xcom_push(key="total_extracted", value=len(clean))
    print(f"[EXTRACT DATAGOUV] {len(clean)} enregistrements extraits")


# ──────────────────────────────────────────────
#  LOAD RAW  (extracted → raw_leads table)
# ──────────────────────────────────────────────
@measure_task
def load_raw_boamp(**context):
    ti = context["ti"]
    run_id  = context.get("run_id", "")
    watermark = ti.xcom_pull(task_ids="scrape_boamp",     key="watermark_start") 
    records = _read(RAW_BOAMP_PATH)
    for item in records:
        item["date_scraping"] = watermark
    db = SessionLocal()
    print("waterrrrrrmaaaaaaak",watermark)
    try:
        inserted = crud.insert_raw_leads(db, records, source="BOAMP", dag_run_id=run_id,date_scraping=watermark)
        _write(RAW_BOAMP_PATH, records)
        if inserted == 0:
            print("[LOAD CLEAN BOAMP] 0 lignes insérées")
    except Exception as e:
        raise   
    finally:
        db.close()
    context["ti"].xcom_push(key="total_raw_loaded", value=inserted)
    print(f"[LOAD RAW BOAMP] {inserted} lignes → raw_leads")

@measure_task
def load_raw_datagouv(**context):
    ti = context["ti"]
    run_id  = context.get("run_id", "")
    watermark = ti.xcom_pull(task_ids="scrape_datagouv",     key="watermark_start") 
    records = _read(RAW_DATAGOUV_PATH)
    for item in records:
        item["date_scraping"] = watermark
    db = SessionLocal()
    print("waterrrrrrmaaaaaaak",watermark)
    try:
        inserted = crud.insert_raw_leads(db, records, source="dataGouv", dag_run_id=run_id, date_scraping=watermark)
        _write(RAW_DATAGOUV_PATH, records)
        if inserted == 0:
            print("[LOAD CLEAN BOAMP] 0 lignes insérées")
    except Exception as e:
        raise 
    finally:
        db.close()
    context["ti"].xcom_push(key="total_raw_loaded", value=inserted)
    print(f"[LOAD RAW DATAGOUV] {inserted} lignes → raw_leads")


# ──────────────────────────────────────────────
#  CLEANING
# ──────────────────────────────────────────────

def _ensure_records_shape(data: list) -> list:
    if not data:
        return []
    first = data[0]
    if isinstance(first, dict) and "entreprise" in first:
        return data
    return [{"entreprise": item, "lead": None} for item in data]

@measure_task
def clean_boamp(**context):
    raw_data = _read(RAW_BOAMP_PATH)
    records  = _ensure_records_shape(raw_data)
    cleaned, report = BoampCleaner().clean(records)
    _write(RAW_BOAMP_PATH, cleaned)
    context["ti"].xcom_push(key="total_clean", value=report.total_cleaned)
    print(f"[CLEAN BOAMP] {report.summary()}")
    for issue in report.issues:
        print(f"  ⚠ index {issue['index']}: {issue['reason']}")

@measure_task
def clean_datagouv(**context):
    raw_data = _read(RAW_DATAGOUV_PATH)
    records  = _ensure_records_shape(raw_data)
    cleaned, report = DataGouvCleaner().clean(records)
    _write(RAW_DATAGOUV_PATH, cleaned)
    context["ti"].xcom_push(key="total_clean", value=report.total_cleaned)
    print(f"[CLEAN DATAGOUV] {report.summary()}")
    for issue in report.issues:
        print(f"  ⚠ index {issue['index']}: {issue['reason']}")


# ──────────────────────────────────────────────
#  LOAD CLEAN  (cleaned → clean_leads table)
# ──────────────────────────────────────────────
@measure_task
def load_clean_boamp(**context):
    ti = context["ti"]
    run_id  = context.get("run_id", "")
    records = _read(RAW_BOAMP_PATH)
    watermark = ti.xcom_pull(task_ids="scrape_boamp",     key="watermark_start")
    for item in records:
        item["date_scraping"] = watermark
    db = SessionLocal()
    print("waterrrrrrmaaaaaaak",watermark)
    try:
        inserted = crud.insert_clean_leads(db, records, source="BOAMP", dag_run_id=run_id, date_scraping=watermark)
        if inserted == 0:
            print("[LOAD CLEAN BOAMP] 0 lignes insérées")
    except Exception as e:
        raise   # ← relance l'exception → Airflow marque la task FAILED
    finally:
        db.close()
    context["ti"].xcom_push(key="total_clean_loaded", value=inserted)
    print(f"[LOAD CLEAN BOAMP] {inserted} lignes → clean_leads")

@measure_task
def load_clean_datagouv(**context):
    ti = context["ti"]
    run_id  = context.get("run_id", "")
    watermark = ti.xcom_pull(task_ids="scrape_datagouv",     key="watermark_start") 
    
    records = _read(RAW_DATAGOUV_PATH)
    for item in records:
        item["date_scraping"] = watermark
    db = SessionLocal()
    print("waterrrrrrmaaaaaaak",watermark)

    try:
        inserted = crud.insert_clean_leads(db, records, source="dataGouv", dag_run_id=run_id,date_scraping=watermark)
        if inserted == 0:
            print("[LOAD CLEAN DATAGOUV] 0 lignes insérées")
    except Exception as e:
        raise   # ← relance l'exception → Airflow marque la task FAILED
    finally:
        db.close()
    context["ti"].xcom_push(key="total_clean_loaded", value=inserted)
    print(f"[LOAD CLEAN DATAGOUV] {inserted} lignes → clean_leads")

@measure_task    
def load_clean_sirene(**context):
    ti = context["ti"]
    run_id  = context.get("run_id", "")
    watermark = ti.xcom_pull(task_ids="scrape_sirene",     key="watermark_start") 
    
    records = _read(RAW_DATAGOUV_PATH)
    for item in records:
        item["date_scraping"] = watermark
    db = SessionLocal()
    print("waterrrrrrmaaaaaaak",watermark)

    try:
        inserted = crud.insert_clean_leads(db, records, source="dataGouv", dag_run_id=run_id,date_scraping=watermark)
        if inserted == 0:
            print("[LOAD CLEAN DATAGOUV] 0 lignes insérées")
    except Exception as e:
        raise   # ← relance l'exception → Airflow marque la task FAILED
    finally:
        db.close()
    context["ti"].xcom_push(key="total_clean_loaded", value=inserted)
    print(f"[LOAD CLEAN DATAGOUV] {inserted} lignes → clean_leads")


# ──────────────────────────────────────────────
#  CLEANUP
# ──────────────────────────────────────────────

def cleanup(**context):
    _delete(RAW_BOAMP_PATH)
    _delete(RAW_DATAGOUV_PATH)
    print("[CLEANUP] Fichiers temporaires supprimés")


# ──────────────────────────────────────────────
#  RAPPORT FINAL
# ──────────────────────────────────────────────
@measure_task
def rapport_final(sources: list, **context):
    ti = context["ti"]
    print("=" * 55)
    print(f"[RAPPORT] Run : {context['run_id']}")

    for s in sources:
        if isinstance(s, dict):
            source          = s["source"]
            task_scrape     = s["task_scrape"]
            task_extract    = s.get("task_extract")
            task_load_raw   = s.get("task_load_raw")
            task_clean      = s.get("task_clean")
            task_load_clean = s.get("task_load_clean")
        else:
            source          = s
            task_scrape     = f"scrape_{s.lower()}"
            task_extract    = f"extract_{s.lower()}"
            task_load_raw   = f"load_raw_{s.lower()}"
            task_clean      = f"clean_{s.lower()}"
            task_load_clean = f"load_clean_{s.lower()}"

        total_raw        = ti.xcom_pull(task_ids=task_scrape,     key="total_raw")       if task_scrape else None
        total_extracted  = ti.xcom_pull(task_ids=task_extract,    key="total_extracted") if task_extract else None
        total_raw_loaded = ti.xcom_pull(task_ids=task_load_raw,   key="total_raw_loaded") if task_load_raw else None
        total_clean      = ti.xcom_pull(task_ids=task_clean,      key="total_clean")     if task_clean else None
        total_cl_loaded  = ti.xcom_pull(task_ids=task_load_clean, key="total_clean_loaded") if task_load_clean else None
        watermark        = ti.xcom_pull(task_ids=task_scrape,     key="watermark_start") if task_scrape else None

        print(
            f"  [{source}]"
            f"  scraped={total_raw}"
            f"  extracted={total_extracted}"
            f"  raw_leads={total_raw_loaded}"
            f"  cleaned={total_clean}"
            f"  clean_leads={total_cl_loaded}"
        )

        if watermark:
            _update_sync(source, watermark, total_clean or 0)

    print("=" * 55)


# ══════════════════════════════════════════════
#  DAG 1 — Chargement initial (ETL complet)
#
#  init_db
#    ├── scrape_boamp → extract_boamp → load_raw_boamp
#    │                              → clean_boamp → load_clean_boamp ──┐
#    │                                                                   ├── rapport_final → cleanup
#    └── scrape_datagouv → extract_datagouv → load_raw_datagouv        │
#                                           → clean_datagouv → load_clean_datagouv ──┘
# ══════════════════════════════════════════════

with DAG(
    dag_id="initial_load",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["initial", "etl"],
) as dag1:

    t_init = PythonOperator(task_id="init_db", python_callable=init_db)

    # ── BOAMP branch ─────────────────────────────────────────
    t_scrape_b     = PythonOperator(task_id="scrape_boamp",       python_callable=scrape_boamp,     op_kwargs={"is_incremental": False})
    t_ext_b        = PythonOperator(task_id="extract_boamp",      python_callable=extract_boamp)
    t_enrich_b     = PythonOperator(task_id="enrich_boamp",       python_callable=enrich_boamp)
    t_load_raw_b   = PythonOperator(task_id="load_raw_boamp",     python_callable=load_raw_boamp)
    
    t_clean_b      = PythonOperator(task_id="clean_boamp",        python_callable=clean_boamp)
    t_load_clean_b = PythonOperator(task_id="load_clean_boamp",   python_callable=load_clean_boamp)

    # ── DataGouv branch ──────────────────────────────────────
    t_scrape_d     = PythonOperator(task_id="scrape_datagouv",    python_callable=scrape_datagouv)
    t_ext_d        = PythonOperator(task_id="extract_datagouv",   python_callable=extract_datagouv)
    t_load_raw_d   = PythonOperator(task_id="load_raw_datagouv",  python_callable=load_raw_datagouv)
    t_clean_d      = PythonOperator(task_id="clean_datagouv",     python_callable=clean_datagouv)
    t_load_clean_d = PythonOperator(task_id="load_clean_datagouv",python_callable=load_clean_datagouv)

    # ── Finalisation ─────────────────────────────────────────
    t_rapport = PythonOperator(
        task_id="rapport_final",
        python_callable=rapport_final,
        op_kwargs={"sources": ["boamp", "datagouv"]},
    )
    t_cleanup = PythonOperator(task_id="cleanup", python_callable=cleanup)

    # ── Wiring ───────────────────────────────────────────────
    # 1. Scraping et Extraction en parallèle
    t_init >> t_scrape_b >> t_ext_b
    t_init >> t_scrape_d >> t_ext_d

    # 2. Synchronisation pour éviter le Rate Limit API DataGouv
    # L'enrichissement BOAMP ne commence que quand DataGouv a libéré l'API
    [t_ext_b, t_ext_d] >> t_enrich_b

    # 3. Traitements suivants
    t_enrich_b >> t_load_raw_b >> t_clean_b >> t_load_clean_b
    t_ext_d >> t_load_raw_d >> t_clean_d >> t_load_clean_d
    
    [t_load_clean_b, t_load_clean_d] >> t_rapport >> t_cleanup


# ══════════════════════════════════════════════
#  DAG 2 — Sync delta DataGouv / Sirene
# ══════════════════════════════════════════════

with DAG(
    dag_id="sync_datagouv",
    start_date=datetime(2026, 3, 27),
    schedule="0 */6 * * *",
    catchup=False,
    tags=["delta", "etl"],
) as dag2:

    t_scrape  = PythonOperator(task_id="scrape_sirene",     python_callable=scrape_sirene)
    t_ext     = PythonOperator(task_id="extract_datagouv",  python_callable=extract_datagouv)
    t_load_r  = PythonOperator(task_id="load_raw_datagouv", python_callable=load_raw_datagouv)
    t_clean   = PythonOperator(task_id="clean_datagouv",    python_callable=clean_datagouv)
    t_load_c  = PythonOperator(task_id="load_clean_sirene", python_callable=load_clean_sirene)
    t_rapport = PythonOperator(task_id="rapport_final",     python_callable=rapport_final, op_kwargs={
        "sources": [{
            "source"         : "datagouv",
            "task_scrape"    : "scrape_sirene",
            "task_extract"   : "extract_datagouv",
            "task_load_raw"  : "load_raw_datagouv",
            "task_clean"     : "clean_datagouv",
            "task_load_clean": "load_clean_datagouv",
        }]
    })
    t_cleanup = PythonOperator(task_id="cleanup", python_callable=cleanup)

    t_scrape >> t_ext >> t_load_r >> t_clean >> t_load_c >> t_rapport >> t_cleanup


# ══════════════════════════════════════════════
#  DAG 3 — Sync delta BOAMP
# ══════════════════════════════════════════════

with DAG(
    dag_id="sync_boamp",
    start_date=datetime(2026, 3, 27),
    schedule="0 6 * * *",
    catchup=False,
    tags=["delta", "etl"],
) as dag3:

    t_scrape  = PythonOperator(task_id="scrape_boamp",        python_callable=scrape_boamp, op_kwargs={"is_incremental": True})
    t_ext     = PythonOperator(task_id="extract_boamp",       python_callable=extract_boamp)
    t_enrich  = PythonOperator(task_id="enrich_boamp",        python_callable=enrich_boamp)
    t_load_r  = PythonOperator(task_id="load_raw_boamp",      python_callable=load_raw_boamp)
    t_clean   = PythonOperator(task_id="clean_boamp",         python_callable=clean_boamp)
    t_load_c  = PythonOperator(task_id="load_clean_boamp",    python_callable=load_clean_boamp)
    t_rapport = PythonOperator(task_id="rapport_final",       python_callable=rapport_final, op_kwargs={
        "sources": [{
            "source"         : "boamp",
            "task_scrape"    : "scrape_boamp",
            "task_extract"   : "extract_boamp",
            "task_load_raw"  : "load_raw_boamp",
            "task_clean"     : "clean_boamp",
            "task_load_clean": "load_clean_boamp",
        }]
    })
    t_cleanup = PythonOperator(task_id="cleanup", python_callable=cleanup)

    t_scrape >> t_ext >> t_enrich >> t_load_r >> t_clean >> t_load_c >> t_rapport >> t_cleanup


# ══════════════════════════════════════════════
#  DAG 4 — Recherche nouveau lead (DataGouv)
# ══════════════════════════════════════════════

with DAG(
    dag_id="search_new_lead",
    start_date=datetime(2026, 3, 27),
    schedule=None,
    catchup=False,
    tags=["delta", "etl"],
) as dag4:

    t_scrape  = PythonOperator(task_id="scrape_datagouv",      python_callable=scrape_datagouv)
    t_ext     = PythonOperator(task_id="extract_datagouv",     python_callable=extract_datagouv)
    t_load_r  = PythonOperator(task_id="load_raw_datagouv",    python_callable=load_raw_datagouv)
    t_clean   = PythonOperator(task_id="clean_datagouv",       python_callable=clean_datagouv)
    t_load_c  = PythonOperator(task_id="load_clean_datagouv",  python_callable=load_clean_datagouv)
    t_rapport = PythonOperator(task_id="rapport_final",        python_callable=rapport_final, op_kwargs={
        "sources": [{
            "source"         : "datagouv",
            "task_scrape"    : "scrape_datagouv",
            "task_extract"   : "extract_datagouv",
            "task_load_raw"  : "load_raw_datagouv",
            "task_clean"     : "clean_datagouv",
            "task_load_clean": "load_clean_datagouv",
        }]
    })
    t_cleanup = PythonOperator(task_id="cleanup", python_callable=cleanup)

    t_scrape >> t_ext >> t_load_r >> t_clean >> t_load_c >> t_rapport >> t_cleanup


# ══════════════════════════════════════════════
#  DAG 5 — Sauvegarde manuel d'un lead (depuis Vue.js)
# ══════════════════════════════════════════════

def load_manual_datagouv(**context):
    """
    Task spéciale pour sauvegarder un lead validé par le commercial depuis le front-end.
    Prend le dictionnaire de l'entreprise via la configuration (dag_run.conf).
    """
    dag_run = context["dag_run"]
    entreprise_data = dag_run.conf.get("entreprise")
    if not entreprise_data:
        raise ValueError("Aucune donnée d'entreprise n'a été transmise dans la configuration")

    run_id = context.get("run_id", "")
    now_str = datetime.now().isoformat()
    db = SessionLocal()
    
    # On reconstruit la structure {"entreprise": ..., "lead": None}
    cr = {"entreprise": entreprise_data, "lead": None, "date_scraping": now_str}
    
    try:
        # Save raw
        crud.insert_raw_leads(db, [entreprise_data], source="dataGouv", dag_run_id=run_id, date_scraping=now_str)
        if entreprise_data.get("_raw_lead_id"):
            cr["entreprise"]["_raw_lead_id"] = entreprise_data.get("_raw_lead_id")
        # Save clean
        inserted = crud.insert_clean_leads(db, [cr], source="dataGouv", dag_run_id=run_id, date_scraping=now_str)
        print(f"[LOAD MANUAL LEAD] {inserted} lignes insérées/mises à jour dans clean_leads")
    finally:
        db.close()


with DAG(
    dag_id="load_manual_lead",
    start_date=datetime(2026, 3, 27),
    schedule=None,
    catchup=False,
    tags=["manual", "etl"],
) as dag5:

    t_load_manual = PythonOperator(task_id="load_manual_datagouv", python_callable=load_manual_datagouv)
    t_load_manual