"""
apis/routers/segmentation.py
============================
Three endpoints for the CEO/Manager Segmentation & Market Analysis page.
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from db.database import get_db

router = APIRouter()

EXPORT_DIR = os.environ.get("SEGMENTATION_EXPORT_DIR", "/opt/airflow/exports/segmentation")
SUMMARY_PATH = Path(EXPORT_DIR) / "cluster_summary.json"
LEADS_PATH   = Path(EXPORT_DIR) / "clustered_leads.json"


# ── POST /segmentation/run ────────────────────────────────────────────────────

@router.post("/run", summary="Run KMeans clustering on all entreprise records")
def run_segmentation(db: Session = Depends(get_db)):
    """
    Reads all Entreprise rows, runs KMeans K=5, writes JSON outputs.
    Synchronous (~2-5 sec for ~1000 rows).
    """
    try:
        from market_analysis.clustering import run_clustering
        result = run_clustering(db)
        return {"status": "ok", "total_rows": result["total_leads"], "run_at": result["run_at"], "segments": result["segments"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")


# ── GET /segmentation/summary ─────────────────────────────────────────────────

@router.get("/summary", summary="Get latest cluster summary (KPIs + segment profiles)")
def get_summary():
    """
    Returns the last computed cluster_summary.json.
    Call POST /run first if this returns 404.
    """
    if not SUMMARY_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No clustering results found. Call POST /segmentation/run first."
        )
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# ── GET /segmentation/leads ───────────────────────────────────────────────────

@router.get("/leads", summary="Get clustered leads with optional filtering")
def get_leads(
    segment: Optional[int] = None,
    search:  Optional[str] = None,
    skip:    int = 0,
    limit:   int = 50,
):
    """
    Returns clustered leads from the last run.
    Filters: segment (cluster int 0-4), search (nom_entreprise substring).
    """
    if not LEADS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No clustering results found. Call POST /segmentation/run first."
        )

    with open(LEADS_PATH, "r", encoding="utf-8") as f:
        leads = json.load(f)

    # Filter
    if segment is not None:
        leads = [l for l in leads if l.get("cluster") == segment]
    if search:
        q = search.lower()
        leads = [l for l in leads if q in (l.get("nom_entreprise") or "").lower()]

    total = len(leads)
    page  = leads[skip: skip + limit]

    # Attach segment label to each lead (already in JSON but ensure present)
    from market_analysis.clustering import SEGMENT_LABELS
    segment_label = SEGMENT_LABELS.get(segment, {}).get("name") if segment is not None else None

    return {
        "total":         total,
        "skip":          skip,
        "limit":         limit,
        "segment_label": segment_label,
        "leads":         page,
    }
