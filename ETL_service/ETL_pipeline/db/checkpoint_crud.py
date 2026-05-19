"""
checkpoint_crud.py — CRUD helpers for `lead_generation_checkpoint`.

One checkpoint row exists per NAF filter_key.  The `generate_new_leads`
DAG reads the checkpoint before each batch to determine which page to
start from, and updates it after a successful batch.

Key guarantee: the checkpoint is NEVER advanced if the batch fails.
This makes every batch safe to retry from exactly the right page.
"""

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models import LeadGenerationCheckpoint

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
#  READ
# ──────────────────────────────────────────────────────────────

def get_checkpoint(db: Session, filter_key: str) -> LeadGenerationCheckpoint | None:
    """
    Fetch the checkpoint row for a given NAF filter_key.
    Returns None if no checkpoint exists yet (i.e. first run for this group).
    """
    try:
        return (
            db.query(LeadGenerationCheckpoint)
            .filter(LeadGenerationCheckpoint.filter_key == filter_key)
            .first()
        )
    except SQLAlchemyError as e:
        logger.error("[CHECKPOINT] get_checkpoint error for key=%r: %s", filter_key, e)
        return None


def get_all_checkpoints(db: Session, source: str = "datagouv") -> list[LeadGenerationCheckpoint]:
    """Return all checkpoint rows for a given source, ordered by filter_key."""
    return (
        db.query(LeadGenerationCheckpoint)
        .filter(LeadGenerationCheckpoint.source == source)
        .order_by(LeadGenerationCheckpoint.filter_key)
        .all()
    )


# ──────────────────────────────────────────────────────────────
#  WRITE
# ──────────────────────────────────────────────────────────────

def upsert_checkpoint(
    db: Session,
    filter_key: str,
    naf_codes: str,
    last_page_fetched: int,
    per_page: int,
    total_results: int | None,
    total_pages: int | None,
    pages_fetched_this_batch: int,
    records_inserted_this_batch: int,
    run_id: str | None = None,
    source: str = "datagouv",
) -> bool:
    """
    Create or update the checkpoint row for a NAF filter_key.

    This must only be called AFTER a batch has been successfully processed.
    Calling it on a failed batch would advance the checkpoint beyond what
    was actually stored, causing pages to be skipped forever.

    Args:
        filter_key              : unique key identifying the NAF group
        naf_codes               : raw activite_principale string for this group
        last_page_fetched       : the last page number that was successfully fetched
        per_page                : page size used (for reference)
        total_results           : total results reported by the API (may be None if API failed early)
        total_pages             : total pages (ceil of total_results/per_page)
        pages_fetched_this_batch: number of pages actually fetched in this run
        records_inserted_this_batch: number of clean rows inserted
        run_id                  : Airflow run_id for traceability
        source                  : 'datagouv' (default)

    Returns:
        True on success, False on DB error.
    """
    try:
        row = (
            db.query(LeadGenerationCheckpoint)
            .filter(LeadGenerationCheckpoint.filter_key == filter_key)
            .first()
        )

        if row is None:
            row = LeadGenerationCheckpoint(
                source            = source,
                filter_key        = filter_key,
                naf_codes         = naf_codes,
                last_page_fetched = last_page_fetched,
                per_page          = per_page,
                total_results     = total_results,
                total_pages       = total_pages,
                total_fetched     = pages_fetched_this_batch * per_page,
                total_inserted    = records_inserted_this_batch,
                last_run_id       = run_id,
            )
            db.add(row)
        else:
            row.last_page_fetched = last_page_fetched
            row.per_page          = per_page
            row.naf_codes         = naf_codes
            if total_results is not None:
                row.total_results = total_results
            if total_pages is not None:
                row.total_pages   = total_pages
            row.total_fetched  += pages_fetched_this_batch * per_page
            row.total_inserted += records_inserted_this_batch
            row.last_run_id    = run_id

        db.commit()
        logger.info(
            "[CHECKPOINT] Saved filter_key=%r | last_page=%d | inserted_this_batch=%d",
            filter_key, last_page_fetched, records_inserted_this_batch,
        )
        return True

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("[CHECKPOINT] upsert_checkpoint DB error for key=%r: %s", filter_key, e)
        return False
    except Exception as e:
        db.rollback()
        logger.error("[CHECKPOINT] Unexpected error for key=%r: %s", filter_key, e)
        return False


def reset_checkpoint(db: Session, filter_key: str) -> bool:
    """
    Completely reset a checkpoint (set last_page_fetched back to 0).
    Used when a commercial user wants to restart discovery from page 1
    for a specific NAF group.
    """
    try:
        row = (
            db.query(LeadGenerationCheckpoint)
            .filter(LeadGenerationCheckpoint.filter_key == filter_key)
            .first()
        )
        if row is None:
            logger.warning("[CHECKPOINT] reset_checkpoint: key=%r not found — nothing to reset.", filter_key)
            return False

        row.last_page_fetched = 0
        row.total_fetched     = 0
        row.total_inserted    = 0
        row.total_results     = None
        row.total_pages       = None
        row.last_run_id       = None
        db.commit()
        logger.info("[CHECKPOINT] Reset filter_key=%r to page 0.", filter_key)
        return True

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("[CHECKPOINT] reset_checkpoint DB error for key=%r: %s", filter_key, e)
        return False


def reset_all_checkpoints(db: Session, source: str = "datagouv") -> int:
    """
    Reset ALL checkpoints for a source back to page 0.
    Returns the number of rows reset.
    """
    try:
        rows = (
            db.query(LeadGenerationCheckpoint)
            .filter(LeadGenerationCheckpoint.source == source)
            .all()
        )
        for row in rows:
            row.last_page_fetched = 0
            row.total_fetched     = 0
            row.total_inserted    = 0
        db.commit()
        logger.info("[CHECKPOINT] Reset %d checkpoints for source=%r.", len(rows), source)
        return len(rows)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("[CHECKPOINT] reset_all_checkpoints error: %s", e)
        return 0
