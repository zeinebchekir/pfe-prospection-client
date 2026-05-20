"""
dag_generate_new_leads.py — Incremental commercial lead generation DAG.

DAG ID      : generate_new_leads
Schedule    : None (triggered on-demand by POST /etl/generate-new-leads)
Tags        : ["incremental", "etl", "commercial"]

Purpose
───────
This DAG is the engine behind the COMMERCIAL "Générer nouveaux leads"
button.  It continues DataGouv pagination from where the LAST run left
off, using per-NAF-group checkpoints stored in `lead_generation_checkpoint`.

It is completely independent of `initial_load` and does NOT restart from
page 1.  Every click of the button fetches the next `pages_per_batch`
pages for each NAF group.

Filter pipeline (in order)
──────────────────────────
1. NAF prefix filter          (filter_by_naf_prefix)
2. Extraction                 (extract_data_from_datagouv)
3. Completeness filter        (filter_by_completeness)
4. PME exclusion              (filter_by_company_size) ← NEW
5. Deduplication by SIREN     (via crud.insert_clean_leads UPSERT logic)

Checkpoint guarantee
────────────────────
- Checkpoint is advanced ONLY after a successful batch.
- If the task fails mid-batch, the checkpoint stays at the previous value.
- On the next run, the batch restarts from the checkpoint page.

Config (injected via DAG run conf)
────────────────────────────────────
  pages_per_batch   : int  (default 5)   — pages per NAF group per run

Task graph
──────────
  init_db → generate_leads_batch → cleanup_tmp
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os
import json
import time
import math
import functools
import psutil

sys.path.insert(0, "/opt/airflow/ETL_pipeline")
sys.path.insert(0, "/opt/airflow/ETL_pipeline/cleaners")

from filters import filter_by_naf_prefix, filter_by_completeness, filter_by_company_size
from scrapers.dataGouv import DataGouvService, _NAF_SECTION_FILTER
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv
from db.database import SessionLocal, create_tables
from db import crud
from db.checkpoint_crud import get_checkpoint, upsert_checkpoint
from db.etl_logger import log_task_start, log_task_success, log_task_failure
from cleaners.dataGouv_cleaner import DataGouvCleaner

# ── Temp file paths ────────────────────────────────────────────
SHARED_DIR      = "/opt/airflow/shared_tmp"
TMP_BATCH_PATH  = os.path.join(SHARED_DIR, "batch_generate_leads.json")
os.makedirs(SHARED_DIR, exist_ok=True)

# ── Defaults ──────────────────────────────────────────────────
DEFAULT_PAGES_PER_BATCH = 5
PER_PAGE                = 25       # items per API page (matches DataGouvService.per_page)
# Toggle this back to True later when LinkedIn enrichment is needed again.
ENABLE_LINKEDIN_ENRICHMENT = False


# ── Decorator ─────────────────────────────────────────────────

def _measure(func):
    """Minimal version of the @measure_task decorator from initial_load."""
    @functools.wraps(func)
    def wrapper(**context):
        ti      = context.get("ti")
        dag_id  = ti.dag_id  if ti else "unknown"
        run_id  = ti.run_id  if ti else "unknown"
        task_id = ti.task_id if ti else func.__name__
        process = psutil.Process(os.getpid())
        start_time = time.time()
        log_task_start(dag_id, run_id, task_id)
        try:
            result = func(**context)
            duration = round(time.time() - start_time, 2)
            cpu = process.cpu_percent(interval=0.1)
            ram = process.memory_info().rss / (1024 ** 2)
            log_task_success(dag_id, run_id, task_id, duration, {
                "cpu_used":    f"{cpu:.1f}%",
                "ram_used_mb": f"{ram:.1f} MB",
            })
            return result
        except Exception as exc:
            duration = round(time.time() - start_time, 2)
            log_task_failure(dag_id, run_id, task_id, duration, exc)
            raise
    return wrapper


# ── Helpers ───────────────────────────────────────────────────

def _write(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _delete(path):
    if os.path.exists(path):
        os.remove(path)


def _make_filter_key(entry: dict) -> str:
    """Stable, readable key for a NAF group dict.  Used as checkpoint PK."""
    naf = entry.get("activite_principale", "unknown")
    return f"datagouv::{naf}"


# ══════════════════════════════════════════════════════════════
#  TASKS
# ══════════════════════════════════════════════════════════════

def init_db(**context):
    """Ensures all tables exist (idempotent).  Runs first."""
    create_tables()
    print("[GENERATE_LEADS] Tables ready.")


@_measure
def generate_leads_batch(**context):
    """
    Core task: for every NAF group in _NAF_SECTION_FILTER, read the checkpoint,
    fetch the next `pages_per_batch` pages, filter, clean, and upsert into DB.
    Advances checkpoint only on success.
    """
    ti       = context["ti"]
    run_id   = context.get("run_id", "")
    dag_run  = context.get("dag_run")
    conf     = dag_run.conf or {} if dag_run else {}

    pages_per_batch: int = int(conf.get("pages_per_batch", DEFAULT_PAGES_PER_BATCH))
    enrich_linkedin_conf = conf.get("enable_linkedin_enrichment", ENABLE_LINKEDIN_ENRICHMENT)
    enrich_linkedin = str(enrich_linkedin_conf).lower() in {"1", "true", "yes", "on"}
    aujourdhui = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    print("=" * 60)
    print(
        f"[GENERATE_LEADS] run_id={run_id} | pages_per_batch={pages_per_batch} "
        f"| enrich_linkedin={enrich_linkedin}"
    )
    print("=" * 60)

    svc = DataGouvService()

    total_raw_all      = 0
    total_naf_kept     = 0
    total_complete     = 0
    total_large        = 0
    total_inserted     = 0
    total_pme_dropped  = 0
    groups_processed   = 0

    all_clean_records: list[dict] = []

    db = SessionLocal()
    try:
        for entry in _NAF_SECTION_FILTER:
            # Copy — NEVER mutate the original
            entry_copy  = dict(entry)
            filter_key  = _make_filter_key(entry_copy)
            naf_codes   = entry_copy.get("activite_principale", "")
            max_pages   = entry_copy.get("_max_pages", 80)

            # Build clean params dict (strip private keys)
            params = {k: v for k, v in entry_copy.items() if not k.startswith("_")}

            # ── Read checkpoint ──────────────────────────────────────
            checkpoint = get_checkpoint(db, filter_key)
            last_page  = checkpoint.last_page_fetched if checkpoint else 0
            start_page = last_page + 1

            print("-" * 60)
            print(f"[NAF GROUP] filter_key={filter_key!r}")
            print(f"  naf_codes  : {naf_codes}")
            print(f"  checkpoint : last_page_fetched={last_page}")
            print(f"  start_page : {start_page}")
            print(f"  end_page   : {start_page + pages_per_batch - 1}")

            # ── Fetch raw pages ──────────────────────────────────────
            raw_items = svc._paginer(
                params=params,
                start_page=start_page,
                pages_to_fetch=pages_per_batch,
                max_pages=max_pages,
            )

            pages_actually_fetched = math.ceil(len(raw_items) / PER_PAGE) if raw_items else 0
            last_page_this_batch   = start_page + pages_actually_fetched - 1 if pages_actually_fetched else last_page

            print(f"  raw_fetched  : {len(raw_items)}")
            total_raw_all += len(raw_items)

            if not raw_items:
                print(f"  [NAF GROUP] No raw items fetched — checkpoint NOT advanced.")
                groups_processed += 1
                time.sleep(svc.delai)
                continue

            # ── STEP 1: NAF prefix filter ────────────────────────────
            naf_kept, naf_dropped = filter_by_naf_prefix(raw_items)
            print(f"  naf_kept     : {len(naf_kept)} | naf_dropped: {naf_dropped}")
            total_naf_kept += len(naf_kept)

            # ── STEP 2: Extraction ───────────────────────────────────
            extracted = extract_data_from_datagouv(
                naf_kept,
                enrich_linkedin=enrich_linkedin,
            )

            # ── STEP 3: Completeness filter ──────────────────────────
            complete_kept, complete_dropped, _drop_log = filter_by_completeness(extracted)
            print(f"  completeness : kept={len(complete_kept)} | dropped={complete_dropped}")
            total_complete += len(complete_kept)

            # ── STEP 4: PME exclusion ────────────────────────────────
            large_kept, pme_dropped, pme_log = filter_by_company_size(complete_kept)
            print(f"  pme_filter   : kept={len(large_kept)} | pme_dropped={pme_dropped}")
            if pme_log:
                for entry_log in pme_log[:10]:
                    print(f"    PME dropped: siren={entry_log['siren']} nom={entry_log['nom']!r} | {entry_log['reason']}")
            total_large       += len(large_kept)
            total_pme_dropped += pme_dropped

            # ── STEP 5: Clean ────────────────────────────────────────
            records_wrapped = [{"entreprise": item, "lead": None} for item in large_kept]
            cleaned_records, report = DataGouvCleaner().clean(records_wrapped)
            print(f"  cleaner      : {report.summary()}")

            # Tag with scraping date
            for rec in cleaned_records:
                rec.get("entreprise", {})["date_scraping"] = aujourdhui

            # ── STEP 6: Insert raw + clean ───────────────────────────
            inserted_raw  = crud.insert_raw_leads(
                db,
                [r.get("entreprise", r) for r in cleaned_records],
                source="dataGouv",
                dag_run_id=run_id,
                date_scraping=aujourdhui,
            )
            inserted_clean = crud.insert_clean_leads(
                db,
                cleaned_records,
                source="dataGouv",
                dag_run_id=run_id,
                date_scraping=aujourdhui,
            )

            print(f"  inserted_raw   : {inserted_raw}")
            print(f"  inserted_clean : {inserted_clean}")
            total_inserted += inserted_clean

            # ── STEP 7: Advance checkpoint (only after success) ──────
            ok = upsert_checkpoint(
                db,
                filter_key                  = filter_key,
                naf_codes                   = naf_codes,
                last_page_fetched           = last_page_this_batch,
                per_page                    = PER_PAGE,
                total_results               = None,   # filled by _paginer if needed
                total_pages                 = None,
                pages_fetched_this_batch    = pages_actually_fetched,
                records_inserted_this_batch = inserted_clean,
                run_id                      = run_id,
            )
            if ok:
                print(f"  checkpoint   : advanced to page {last_page_this_batch} ✅")
            else:
                print(f"  checkpoint   : ERROR advancing checkpoint — will retry next run ⚠️")

            groups_processed += 1
            time.sleep(svc.delai)

    finally:
        db.close()

    # ── Summary XCom ──────────────────────────────────────────
    print("=" * 60)
    print(f"[GENERATE_LEADS] SUMMARY")
    print(f"  groups_processed : {groups_processed}")
    print(f"  total_raw_all    : {total_raw_all}")
    print(f"  total_naf_kept   : {total_naf_kept}")
    print(f"  total_complete   : {total_complete}")
    print(f"  total_pme_dropped: {total_pme_dropped}")
    print(f"  total_large      : {total_large}")
    print(f"  total_inserted   : {total_inserted}")
    print("=" * 60)

    ti.xcom_push(key="total_raw",            value=total_raw_all)
    ti.xcom_push(key="total_naf_kept",       value=total_naf_kept)
    ti.xcom_push(key="total_complete",       value=total_complete)
    ti.xcom_push(key="total_pme_dropped",    value=total_pme_dropped)
    ti.xcom_push(key="total_inserted",       value=total_inserted)
    ti.xcom_push(key="groups_processed",     value=groups_processed)


def cleanup_tmp(**context):
    """Remove any leftover temp files."""
    _delete(TMP_BATCH_PATH)
    print("[GENERATE_LEADS] Temp files cleaned.")


# ══════════════════════════════════════════════════════════════
#  DAG DEFINITION
# ══════════════════════════════════════════════════════════════
#
#  schedule=None  — NEVER runs on cron.
#  Triggered exclusively via:
#    - POST /etl/generate-new-leads  (FastAPI)
#    - Airflow UI: http://localhost:8080 → DAG generate_new_leads
#
#  Config (dag_run.conf):
#    pages_per_batch : int  (default=5)
#
# ══════════════════════════════════════════════════════════════

with DAG(
    dag_id="generate_new_leads",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["incremental", "etl", "commercial"],
    doc_md=__doc__,
) as dag:

    t_init    = PythonOperator(task_id="init_db",               python_callable=init_db)
    t_batch   = PythonOperator(task_id="generate_leads_batch",  python_callable=generate_leads_batch)
    t_cleanup = PythonOperator(task_id="cleanup_tmp",           python_callable=cleanup_tmp)

    t_init >> t_batch >> t_cleanup
