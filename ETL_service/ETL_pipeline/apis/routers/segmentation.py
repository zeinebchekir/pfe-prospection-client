"""
Segmentation endpoints.

The public routes remain unchanged even though the backend engine now uses a
decision tree instead of KMeans.
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from market_analysis.text_utils import repair_text_payload

router = APIRouter()

EXPORT_DIR = os.environ.get(
    "SEGMENTATION_EXPORT_DIR", "/opt/airflow/exports/segmentation"
)
SUMMARY_PATH = Path(EXPORT_DIR) / "cluster_summary.json"
LEADS_PATH = Path(EXPORT_DIR) / "clustered_leads.json"
INSIGHTS_PATH = Path(EXPORT_DIR) / "cluster_insights.json"


@router.post("/run", summary="Run segmentation pipeline")
def run_segmentation(db: Session = Depends(get_db)):
    """
    Full pipeline: fetch DB -> segment -> validate -> explain -> insights -> save.
    Returns the same payload written to cluster_summary.json.
    """
    try:
        from market_analysis.clustering import run_clustering

        return run_clustering(db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        import traceback

        raise HTTPException(
            status_code=500,
            detail=f"Segmentation failed: {str(exc)}\n{traceback.format_exc()}",
        )


@router.get(
    "/summary",
    summary="Latest segmentation summary with insights and validation metrics",
)
def get_summary():
    """
    Returns cluster_summary.json including:
    - total_rows, total_leads, run_at, k_used, model_type
    - segments[] with label, color, stats, explainability
    - validation{} model metrics
    - insights[] from Gemini or fallback
    """
    if not SUMMARY_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No segmentation results found. Call POST /segmentation/run first.",
        )

    with open(SUMMARY_PATH, "r", encoding="utf-8") as handle:
        data = repair_text_payload(json.load(handle))

    if not data.get("insights") and INSIGHTS_PATH.exists():
        try:
            with open(INSIGHTS_PATH, "r", encoding="utf-8") as handle:
                insights_payload = repair_text_payload(json.load(handle))
            data["insights"] = insights_payload.get("insights", [])
            data["insights_source"] = insights_payload.get(
                "source", data.get("insights_source", "")
            )
        except Exception:
            data["insights"] = []

    data.setdefault("status", "ok")
    data.setdefault("model_type", "kmeans")
    data.setdefault("total_rows", data.get("total_leads"))
    return data


@router.get("/leads", summary="Paginated + filterable segmented leads")
def get_leads(
    segment: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
):
    if not LEADS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No segmentation results found. Call POST /segmentation/run first.",
        )

    with open(LEADS_PATH, "r", encoding="utf-8") as handle:
        leads = repair_text_payload(json.load(handle))

    if segment is not None:
        leads = [lead for lead in leads if lead.get("cluster") == segment]
    if search:
        query = search.lower()
        leads = [
            lead
            for lead in leads
            if query in (lead.get("nom_entreprise") or "").lower()
        ]

    total = len(leads)
    page = leads[skip : skip + limit]

    segment_label = None
    if segment is not None and SUMMARY_PATH.exists():
        try:
            with open(SUMMARY_PATH, "r", encoding="utf-8") as handle:
                summary = repair_text_payload(json.load(handle))
            segment_map = {
                seg["cluster"]: seg["label"] for seg in summary.get("segments", [])
            }
            segment_label = segment_map.get(segment)
        except Exception:
            pass

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "segment_label": segment_label,
        "leads": page,
    }


@router.get("/validation", summary="Model validation metrics")
def get_validation():
    """Returns the validation block from the latest segmentation run."""
    if not SUMMARY_PATH.exists():
        raise HTTPException(status_code=404, detail="No segmentation results found.")

    with open(SUMMARY_PATH, "r", encoding="utf-8") as handle:
        data = repair_text_payload(json.load(handle))

    validation = data.get("validation")
    if not validation:
        raise HTTPException(
            status_code=404,
            detail="Validation metrics not available. Re-run segmentation.",
        )

    return {
        "run_at": data.get("run_at"),
        "k_used": data.get("k_used", len(data.get("segments", []))),
        "model_type": data.get("model_type", validation.get("model_type", "kmeans")),
        "validation": validation,
    }
