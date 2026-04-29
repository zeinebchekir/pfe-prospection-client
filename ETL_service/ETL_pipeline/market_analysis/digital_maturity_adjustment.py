"""
market_analysis/digital_maturity_adjustment.py
===============================================
Step 2 of the Hybrid Digital Maturity model.

Computes per-dimension ADJUSTMENTS to the sector baseline using the
internal company data already available from the clustering pipeline.

Architecture:
  final_score = baseline + adjustment (+ optional LLM delta, bounded)
  This file covers ONLY the adjustment layer.

Rules:
  - All adjustments are ADDITIVE (can be negative)
  - Each adjustment is bounded to prevent any single signal from dominating
  - Total adjustment per dimension is clamped to [-2.5, +2.5]
  - Reasons are stored as human-readable French strings (CEO-visible)

Usage:
  from market_analysis.digital_maturity_adjustment import compute_adjustment
  result = compute_adjustment(segment_dict)
  # → {
  #     "adjustments": {"tech": +0.8, "data": +0.4, ...},
  #     "reasons": ["CA très élevé (+tech +data)", ...]
  #   }
"""

from __future__ import annotations

DIMENSIONS = ("tech", "data", "process", "culture", "cx")

# Max magnitude a single rule may contribute per dimension
_MAX_RULE_DELTA = 1.0

# Total adjustment clamp per dimension (safety net)
_MAX_TOTAL_DELTA = 2.5


def compute_adjustment(segment: dict) -> dict:
    """
    Compute maturity dimension adjustments from internal segment aggregates.

    Args:
        segment: cluster summary dict containing at minimum:
            - employes_moyen     (float | None)
            - ca_moyen           (float | None)
            - nb_locaux_moyen    (float | None)
            - age_moyen          (float | None)
            - categorie_dominante (str | None)
            - secteur_dominant   (str | None)
            - n                  (int) — lead count

    Returns:
        {
            "adjustments": {dim: float},   # per-dimension deltas
            "reasons": [str]               # CEO-readable explanations
        }
    """
    adj: dict[str, float] = {d: 0.0 for d in DIMENSIONS}
    reasons: list[str] = []

    emp  = _safe_float(segment.get("employes_moyen"))
    ca   = _safe_float(segment.get("ca_moyen"))
    loc  = _safe_float(segment.get("nb_locaux_moyen"))
    age  = _safe_float(segment.get("age_moyen"))
    cat  = (segment.get("categorie_dominante") or "").lower()
    n    = int(segment.get("n") or 0)

    # ── Rule 1: Very large company (headcount) ─────────────────────────────
    # Large organisations have had to invest in tech and process infrastructure.
    if emp is not None and emp >= 1000:
        _add(adj, "tech",    +0.8)
        _add(adj, "process", +0.7)
        _add(adj, "data",    +0.4)
        reasons.append(f"Effectif très élevé ({int(emp)} salariés) → suggère une capacité accrue à structurer les systèmes et processus IT (+tech +process +data)")

    elif emp is not None and emp >= 200:
        _add(adj, "tech",    +0.5)
        _add(adj, "process", +0.4)
        reasons.append(f"Effectif significatif ({int(emp)} salariés) → indique un besoin d'outils digitaux pour la collaboration (+tech +process)")

    elif emp is not None and emp >= 50:
        _add(adj, "tech",    +0.2)
        _add(adj, "process", +0.2)
        reasons.append(f"Effectif intermédiaire ({int(emp)} salariés) → structuration digitale opérationnelle probable (+tech +process)")

    elif emp is not None and emp < 10:
        # Very small → likely limited digital infrastructure
        _add(adj, "tech",    -0.3)
        _add(adj, "process", -0.3)
        reasons.append(f"Très petite structure ({int(emp)} salariés) → les ressources IT sont souvent limitées à l'essentiel (-tech -process)")

    # ── Rule 2: Revenue level ──────────────────────────────────────────────
    # High CA companies can afford digital investments; also signals ERP maturity.
    if ca is not None and ca >= 1e9:
        _add(adj, "tech",    +0.8)
        _add(adj, "data",    +0.7)
        _add(adj, "process", +0.5)
        reasons.append(f"CA très élevé ({_fmt_ca(ca)}) → indique généralement une capacité d'investissement dans des infrastructures lourdes (+tech +data)")

    elif ca is not None and ca >= 1e8:
        _add(adj, "tech",    +0.4)
        _add(adj, "data",    +0.4)
        reasons.append(f"CA significatif ({_fmt_ca(ca)}) → suggère un budget allouable à la transformation IT (+tech +data)")

    elif ca is not None and ca >= 1e7:
        _add(adj, "tech",    +0.2)
        _add(adj, "data",    +0.1)
        reasons.append(f"CA modéré ({_fmt_ca(ca)}) → tend vers des investissements digitaux ciblés sur l'opérationnel (+tech +data)")

    elif ca is not None and ca < 1e6 and ca > 0:
        # Very low CA → likely minimal digital stack
        _add(adj, "tech",    -0.3)
        _add(adj, "data",    -0.3)
        reasons.append(f"CA faible ({_fmt_ca(ca)}) → budget souvent restreint limitant les investissements IT complexes (-tech -data)")

    # ── Rule 3: Multi-site organisation ───────────────────────────────────
    # Multi-site companies MUST have centralised IT, workflows, and communication tools.
    if loc is not None and loc >= 50:
        _add(adj, "process", +0.8)
        _add(adj, "tech",    +0.4)
        reasons.append(f"Organisation multi-sites ({int(loc)} locaux) → nécessite quasi-systématiquement un SI centralisé (+process +tech)")

    elif loc is not None and loc >= 10:
        _add(adj, "process", +0.5)
        _add(adj, "tech",    +0.2)
        reasons.append(f"Présence multi-sites ({int(loc)} locaux) → requiert des opérations digitalisées pour la bonne coordination (+process)")

    elif loc is not None and loc >= 3:
        _add(adj, "process", +0.2)
        reasons.append(f"Plusieurs sites ({int(loc)}) → suggère l'usage croissant d'outils collaboratifs distants (+process)")

    # ── Rule 4: Company age ────────────────────────────────────────────────
    # Young companies are "digital-native" by default; very old ones may lag.
    if age is not None and age <= 10:
        _add(adj, "culture", +0.6)
        _add(adj, "cx",      +0.4)
        reasons.append(f"Entreprise jeune ({age:.0f} ans) → tend vers des processus et une culture cloud-native par défaut (+culture +cx)")

    elif age is not None and age <= 20:
        _add(adj, "culture", +0.3)
        reasons.append(f"Entreprise récente ({age:.0f} ans) → indique généralement une agilité favorisant l'adoption technique (+culture)")

    elif age is not None and age >= 60:
        _add(adj, "culture", -0.4)
        _add(adj, "cx",      -0.2)
        reasons.append(f"Organisation historique ({age:.0f} ans) → doit souvent gérer un patrimoine technique (legacy) complexe à moderniser (-culture)")

    elif age is not None and age >= 40:
        _add(adj, "culture", -0.2)
        reasons.append(f"Organisation établie ({age:.0f} ans) → l'intégration de nouvelles technos peut requérir une forte conduite du changement (-culture)")

    # ── Rule 5: Legal category ─────────────────────────────────────────────
    # Large Entreprise and ETI have formal IT governance frameworks.
    if "grande entreprise" in cat:
        _add(adj, "tech",    +0.5)
        _add(adj, "data",    +0.4)
        _add(adj, "process", +0.3)
        reasons.append("Grande Entreprise → possède souvent une structure formelle favorisant l'IT d'entreprise (+tech +data)")

    elif "entreprise de taille intermédiaire" in cat or "eti" in cat:
        _add(adj, "tech",    +0.3)
        _add(adj, "data",    +0.2)
        reasons.append("ETI → signale une complexité nécessitant des outils robustes (ex: ERP central) (+tech +data)")

    elif "petite et moyenne entreprise" in cat or "pme" in cat:
        # Neutral — PME baseline is already average
        pass

    elif "microentreprise" in cat or "tpe" in cat:
        _add(adj, "tech",    -0.4)
        _add(adj, "data",    -0.4)
        _add(adj, "process", -0.3)
        reasons.append("TPE/Microentreprise → indique que les outils digitaux sont la plupart du temps limités à l'essentiel (-tech -data)")

    # ── Rule 6: Data completeness ─────────────────────────────────────────
    # If the company's own record is well-filled, it suggests structured data practices.
    completeness_delta = _data_completeness_bonus(segment)
    if completeness_delta > 0.0:
        _add(adj, "data", +completeness_delta)
        reasons.append(f"Données de profil exhaustives → témoigne indirectement d'une certaine maturité dans la gestion de l'information (+data)")

    # ── Rule 7: Cluster volume ─────────────────────────────────────────────
    # Large clusters provide stronger statistical confidence.
    # This does NOT affect scores — only a confidence note.
    # (Reserved for future calibration)

    # ── Clamp adjustments ─────────────────────────────────────────────────
    for dim in DIMENSIONS:
        adj[dim] = max(-_MAX_TOTAL_DELTA, min(_MAX_TOTAL_DELTA, adj[dim]))
        adj[dim] = round(adj[dim], 2)

    return {
        "adjustments": adj,
        "reasons":     reasons if reasons else ["Données insuffisantes pour affiner le score"],
    }


# ── Private helpers ────────────────────────────────────────────────────────────

def _add(adj: dict, dim: str, delta: float) -> None:
    """Safely accumulate a bounded adjustment on a single dimension."""
    delta = max(-_MAX_RULE_DELTA, min(_MAX_RULE_DELTA, delta))
    adj[dim] = adj.get(dim, 0.0) + delta


def _safe_float(v) -> float | None:
    """Convert value to float or return None."""
    try:
        f = float(v)
        return f if f == f else None   # NaN check
    except (TypeError, ValueError):
        return None


def _data_completeness_bonus(segment: dict) -> float:
    """
    Return a +data bonus based on how many key fields are non-null.
    Max bonus: +0.6 (when all 4 key fields are populated).
    """
    fields = ["employes_moyen", "ca_moyen", "nb_locaux_moyen", "age_moyen"]
    present = sum(1 for f in fields if segment.get(f) not in (None, float("nan"), ""))
    # +0.15 per present field, max +0.6
    return round(present * 0.15, 2)


def _fmt_ca(v: float) -> str:
    """Format CA for reason strings."""
    if v >= 1e9:
        return f"{v / 1e9:.1f} Md€"
    if v >= 1e6:
        return f"{v / 1e6:.0f} M€"
    if v >= 1e3:
        return f"{v / 1e3:.0f} k€"
    return f"{v:.0f} €"
