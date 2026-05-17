"""
FastAPI routes for Segmentation & Market Analysis.

This router exposes the batch segmentation workflow to the frontend. It does
not run ETL ingestion itself; instead, it reads the already-populated ETL
database, triggers the decision-tree segmentation pipeline on demand, and
serves the latest JSON exports back to the Vue dashboard.
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
    Trigger a full segmentation run on the current ETL dataset.

    Args:
        db: Injected SQLAlchemy session connected to the ETL database.

    Returns:
        dict: Summary payload identical to the generated `cluster_summary.json`.

    Error cases:
        400: No usable data or not enough labeled rows to train the tree.
        500: Unexpected runtime error during segmentation or export.
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
    Return the latest segmentation summary for the dashboard landing page.

    Response structure:
        - run metadata (`run_at`, `model_type`, `k_used`)
        - portfolio counts (`total_rows`, `total_leads`)
        - `segments[]` cards with maturity, explainability, and drilldown data
        - `validation` metrics
        - `insights[]` plus `insights_source`

    Error cases:
        404: No segmentation export has been generated yet.
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
    """
    Return a paginated, optionally filtered slice of `clustered_leads.json`.

    Args:
        segment: Optional numeric segment id used to filter one segment.
        search: Optional case-insensitive substring filter on company name.
        skip: Zero-based offset into the filtered lead list.
        limit: Maximum number of leads to return.

    Returns:
        dict: `total`, `skip`, `limit`, optional `segment_label`, and `leads[]`.

    Error cases:
        404: No lead export exists yet because segmentation has not been run.
    """
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
    """
    Return only the validation portion of the latest segmentation summary.

    Returns:
        dict: Run metadata plus the `validation` block used by badges, QA, and
        developer troubleshooting.

    Error cases:
        404: No summary export exists, or the summary has no validation block.
    """
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
