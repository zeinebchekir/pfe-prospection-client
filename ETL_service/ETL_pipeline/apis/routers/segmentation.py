"""
apis/routers/segmentation.py  (v2)
====================================
Four endpoints — backward compatible with v1 + new /validation endpoint.

POST /segmentation/run      → run full pipeline (cluster + validate + LLM)
GET  /segmentation/summary  → latest summary WITH insights + validation
GET  /segmentation/leads    → paginated, filtered leads
GET  /segmentation/validation → model metrics only (silhouette, elbow)
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db

router = APIRouter()

EXPORT_DIR   = os.environ.get("SEGMENTATION_EXPORT_DIR", "/opt/airflow/exports/segmentation")
SUMMARY_PATH = Path(EXPORT_DIR) / "cluster_summary.json"
LEADS_PATH   = Path(EXPORT_DIR) / "clustered_leads.json"
INSIGHTS_PATH= Path(EXPORT_DIR) / "cluster_insights.json"


# ── POST /segmentation/run ────────────────────────────────────────────────────

@router.post("/run", summary="Run KMeans pipeline (cluster + validate + LLM insights)")
def run_segmentation(db: Session = Depends(get_db)):
    """
    Full pipeline: fetch DB → cluster → validate → explain → LLM insights → save.
    Synchronous. Returns full summary on completion.
    """
    try:
        from market_analysis.clustering import run_clustering
        result = run_clustering(db)
        return {
            "status":    "ok",
            "run_at":    result["run_at"],
            "k_used":    result.get("k_used", 5),
            "total_rows": result["total_leads"],
            "silhouette": result.get("validation", {}).get("silhouette"),
            "segments":  result["segments"],
            "insights":  result.get("insights", []),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}\n{traceback.format_exc()}")


# ── GET /segmentation/summary ─────────────────────────────────────────────────

@router.get("/summary", summary="Latest cluster summary with insights and validation metrics")
def get_summary():
    """
    Returns cluster_summary.json including:
    - total_leads, run_at, k_used
    - segments[] with label, color, stats, explainability
    - validation{} silhouette + elbow
    - insights[] from Gemini or fallback
    """
    if not SUMMARY_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No clustering results found. Call POST /segmentation/run first.",
        )
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # If insights are stored separately (older run), merge them
    if not data.get("insights") and INSIGHTS_PATH.exists():
        try:
            with open(INSIGHTS_PATH, "r", encoding="utf-8") as f:
                ins = json.load(f)
            data["insights"] = ins.get("insights", [])
        except Exception:
            data["insights"] = []

    return data


# ── GET /segmentation/leads ───────────────────────────────────────────────────

@router.get("/leads", summary="Paginated + filterable clustered leads")
def get_leads(
    segment: Optional[int] = None,
    search:  Optional[str] = None,
    skip:    int = 0,
    limit:   int = 20,
):
    if not LEADS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No clustering results found. Call POST /segmentation/run first.",
        )

    with open(LEADS_PATH, "r", encoding="utf-8") as f:
        leads = json.load(f)

    if segment is not None:
        leads = [l for l in leads if l.get("cluster") == segment]
    if search:
        q = search.lower()
        leads = [l for l in leads if q in (l.get("nom_entreprise") or "").lower()]

    total = len(leads)
    page  = leads[skip: skip + limit]

    # Segment label from summary if available
    segment_label = None
    if segment is not None and SUMMARY_PATH.exists():
        try:
            with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
                summary = json.load(f)
            seg_map = {s["cluster"]: s["label"] for s in summary.get("segments", [])}
            segment_label = seg_map.get(segment)
        except Exception:
            pass

    return {
        "total":         total,
        "skip":          skip,
        "limit":         limit,
        "segment_label": segment_label,
        "leads":         page,
    }


# ── GET /segmentation/validation ─────────────────────────────────────────────

@router.get("/validation", summary="Model validation metrics (silhouette + elbow)")
def get_validation():
    """
    Returns only the model validation block from the latest clustering run.
    Useful for the data scientist view without the full payload.
    """
    if not SUMMARY_PATH.exists():
        raise HTTPException(status_code=404, detail="No clustering results found.")
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    val = data.get("validation")
    if not val:
        raise HTTPException(status_code=404, detail="Validation metrics not available (legacy run). Re-run clustering.")
    return {
        "run_at":    data.get("run_at"),
        "k_used":    data.get("k_used", 5),
        "validation": val,
    }
