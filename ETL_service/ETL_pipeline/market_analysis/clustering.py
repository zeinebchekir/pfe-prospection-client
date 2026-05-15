"""
Compatibility wrapper for the segmentation engine.

The public entry point stays `run_clustering(db)` because the FastAPI router
and frontend already depend on that name. Internally, the implementation now
delegates to the decision-tree segmentation pipeline instead of KMeans.
"""

from __future__ import annotations

from market_analysis.decision_tree_segmentation import (
    DEFAULT_EXPORT_DIR,
    run_decision_tree_segmentation,
)


def run_clustering(db, export_dir: str = DEFAULT_EXPORT_DIR) -> dict:
    return run_decision_tree_segmentation(db, export_dir=export_dir)
