"""
market_analysis/labeling.py  (v3 — clean naming UX)
=====================================================
Produces TWO label fields per segment:
  - label_short : short CEO-readable primary label  ("Grands groupes")
  - label_sub   : secondary qualifier               ("Segment élevé")
  - label       : kept for backward-compat          = label_short (no qualifiers)

The collision-resolution NO LONGER appends ugly "(Grand)" suffixes to `label`.
Instead it writes to `label_sub` so the UI can render them hierarchically.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from collections import defaultdict


# ── Color palette ────────────────────────────────────────────────────────────
_PALETTE = ["#303E8C", "#04ADBF", "#F29F05", "#56A632", "#2D3773",
            "#E55353", "#7C3AED", "#0891B2", "#059669", "#D97706"]

# ── Primary short label → recommendation ─────────────────────────────────────
_RECOMMENDATION_MAP = {
    "Grands groupes":      "Enterprise focus — cycles longs, RDV C-level",
    "ETI":                 "Relationship selling — account-based marketing",
    "PME":                 "Vertical niche — offre sectorielle dédiée",
    "Microentreprises":    "Long-tail — faible priorité immédiate",
    "Petites structures":  "Self-serve + automation — volume élevé",
}

# ── Sub-qualifier labels ranked by CA within a collision group ────────────────
_SUB_QUALIFIERS = [
    "Segment élevé",        # highest CA in the group
    "Segment intermédiaire",
    "Segment émergent",
    "Segment spécialisé",
    "Segment niche",
]


# ── Public API ────────────────────────────────────────────────────────────────

def assign_labels(summary_rows: list[dict], df: pd.DataFrame) -> list[dict]:
    """
    Assign display labels to each cluster summary row.

    Returns rows with ADDED fields:
      label       → short primary name (e.g. "Grands groupes")
      label_short → identical to label (for explicit use)
      label_sub   → secondary qualifier (e.g. "Segment élevé"), or ""
      color       → hex color from palette
      recommendation → sales strategy string
    """
    ca_vals  = df["chiffre_affaires"].dropna()
    emp_vals = df["nb_employes_mid"].dropna()
    age_vals = df["age_entreprise"].dropna()

    ca_p33,  ca_p66  = np.percentile(ca_vals,  [33, 66])
    emp_p33, emp_p66 = np.percentile(emp_vals, [33, 66])
    age_p50          = np.percentile(age_vals, 50)

    # First pass — derive short primary label
    candidates = []
    for i, row in enumerate(summary_rows):
        ca  = row.get("ca_moyen")      or 0.0
        emp = row.get("employes_moyen") or 0
        age = row.get("age_moyen")     or 0.0

        short = _derive_short_label(ca, emp, age, ca_p33, ca_p66, emp_p33, emp_p66, age_p50)
        rec   = _RECOMMENDATION_MAP.get(short, "Analyser plus en détail")

        candidates.append({
            **row,
            "label":       short,
            "label_short": short,
            "label_sub":   "",          # filled by second pass if needed
            "color":       _PALETTE[i % len(_PALETTE)],
            "recommendation": rec,
            "_ca":  ca,
            "_emp": emp,
        })

    # Second pass — resolve label collisions → populate label_sub
    _resolve_collisions(candidates)

    # Strip internal keys
    for c in candidates:
        c.pop("_ca",  None)
        c.pop("_emp", None)

    return candidates


# ── Helpers ───────────────────────────────────────────────────────────────────

def _derive_short_label(ca, emp, age, ca_p33, ca_p66, emp_p33, emp_p66, age_p50) -> str:
    """
    Map a cluster's stats to a clean 1-2 word CEO label.

    Hierarchy:
      High (≥ p66 for CA or employees)  → "Grands groupes"
      Mid  (≥ p33 for CA or employees)  → "ETI"
      Small + decent size               → "PME"
      Old & tiny                        → "Microentreprises"
      default                           → "Petites structures"
    """
    high_size = (ca >= ca_p66) or (emp >= emp_p66)
    mid_size  = (ca >= ca_p33) or (emp >= emp_p33)
    mature    = age >= age_p50

    if high_size:
        return "Grands groupes"
    if mid_size:
        return "ETI"
    if emp >= emp_p33 * 0.5 and ca >= ca_p33 * 0.3:
        return "PME"
    if mature:
        return "Microentreprises"
    return "Petites structures"


def _resolve_collisions(rows: list[dict]) -> None:
    """
    When multiple clusters share the same `label`, assign `label_sub` to
    distinguish them by their relative CA rank within the collision group.

    E.g.  three "Grands groupes" clusters get:
          label_sub = "Segment élevé", "Segment intermédiaire", "Segment émergent"

    `label` (primary) is NEVER changed — keeping the UI clean.
    """
    groups: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(rows):
        groups[r["label"]].append(i)

    for label, indices in groups.items():
        if len(indices) == 1:
            continue  # unique — no sub-label needed

        # Rank by CA descending within the group
        ranked = sorted(indices, key=lambda i: rows[i]["_ca"] or 0, reverse=True)
        for rank, idx in enumerate(ranked):
            sub = _SUB_QUALIFIERS[rank] if rank < len(_SUB_QUALIFIERS) else f"Sous-segment {rank + 1}"
            rows[idx]["label_sub"] = sub
