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
    """
    Run the production segmentation pipeline through the legacy entry point.

    This wrapper keeps the historical `run_clustering()` API stable even though
    the real implementation now lives in the decision-tree module.

    Args:
        db: Active SQLAlchemy session used to read ETL company rows.
        export_dir: Directory where latest and versioned JSON exports are saved.

    Returns:
        dict: Summary payload also persisted as `cluster_summary.json`.

    Side effects:
        Writes segmentation export files under `export_dir`.
    """
    return run_decision_tree_segmentation(db, export_dir=export_dir)
