"""
market_analysis/digital_maturity.py
=====================================
Step 3 of the Hybrid Digital Maturity model.

Orchestrates the full maturity computation for a segment:
  1. Fetch sector baseline (digital_maturity_baseline.py)
  2. Compute internal adjustment (digital_maturity_adjustment.py)
  3. Add dimensions → clamp to [0, 10]
  4. Compute global score (mean of 5 dimensions)
  5. Derive level (Faible / Moyen / Élevé)
  6. Compute digital_gap = 10 - global_score
  7. Infer maturity_distribution (% Faible/Moyen/Élevé) from score variance

Architecture:
  deterministic baseline + deterministic adjustment = final scores
  LLM layer (optional, bounded) is handled separately in digital_maturity_llm.py

Usage:
  from market_analysis.digital_maturity import compute_maturity
  enriched_segment = compute_maturity(segment_dict)
"""

from __future__ import annotations

from market_analysis.digital_maturity_baseline   import get_sector_baseline, DIMENSIONS
from market_analysis.digital_maturity_adjustment import compute_adjustment

# ── Level thresholds ───────────────────────────────────────────────────────────
_LEVEL_THRESHOLDS: list[tuple[float, str]] = [
    (8.0, "Élevé"),
    (5.0, "Moyen"),
    (0.0, "Faible"),
]

# ── Maturity stage labels (optional extended view) ─────────────────────────────
_STAGES: list[tuple[float, str]] = [
    (9.0, "Optimisé"),
    (7.5, "Avancé"),
    (5.5, "En développement"),
    (3.5, "Initial"),
    (0.0, "Absent"),
]


def compute_maturity(segment: dict) -> dict:
    """
    Enrich a cluster summary dict with digital maturity fields.

    Adds the following keys to the segment dict (never removes existing ones):
        digital_maturity_score   : float  — global score 0–10 (1 decimal)
        digital_maturity_level   : str    — "Faible" | "Moyen" | "Élevé"
        digital_gap              : float  — 10 - score (1 decimal)
        maturity_details : dict  — {
            dimensions           : {tech, data, process, culture, cx}
            maturity_distribution: {faible: %, moyen: %, eleve: %}
            adjustment_reasons   : [str]
            maturity_stage       : str    — "Optimisé" | ... | "Absent"
        }

    Args:
        segment: cluster summary dict (output of assign_labels in labeling.py)

    Returns:
        segment dict with maturity fields added in-place (also returned).
    """
    sector = segment.get("secteur_dominant") or ""

    # 1. Sector baseline
    baseline = get_sector_baseline(sector)

    # 2. Internal adjustments
    adj_result   = compute_adjustment(segment)
    adjustments  = adj_result["adjustments"]
    reasons      = adj_result["reasons"]

    # 3. Combine & clamp per dimension
    dim_scores: dict[str, float] = {}
    for dim in DIMENSIONS:
        raw = baseline.get(dim, 5.0) + adjustments.get(dim, 0.0)
        dim_scores[dim] = round(max(0.0, min(10.0, raw)), 2)

    # 4. Global score (mean of 5 dims)
    global_score = round(sum(dim_scores.values()) / len(DIMENSIONS), 1)

    # 5. Level
    level = _score_to_level(global_score)

    # 6. Digital gap
    gap = round(10.0 - global_score, 1)

    # 7. Maturity distribution (inferred from score spread)
    distribution = _infer_distribution(global_score, dim_scores)

    # 8. Stage
    stage = _score_to_stage(global_score)

    # Enrich the segment dict
    segment["digital_maturity_score"] = global_score
    segment["digital_maturity_level"] = level
    segment["digital_gap"]            = gap
    segment["maturity_details"] = {
        "dimensions":            dim_scores,
        "maturity_distribution": distribution,
        "adjustment_reasons":    reasons,
        "maturity_stage":        stage,
    }

    return segment


def compute_lead_maturity(lead: dict, segment_maturity_score: float, segment_maturity_level: str) -> dict:
    """
    Quickly enrich a single clustered_lead record with maturity fields,
    derived from its parent segment's computed scores.

    We do NOT re-run the full baseline+adjustment pipeline per lead
    (that would be expensive and the lead doesn't have aggregate fields).
    Instead, we propagate the segment-level score with a small Gaussian
    jitter to make individual leads feel distinct while keeping values
    representative.

    Args:
        lead: individual lead dict from clustered_leads.json
        segment_maturity_score: the parent cluster's global_score
        segment_maturity_level: the parent cluster's level string

    Returns:
        lead dict with maturity fields added in-place (also returned).
    """
    import random
    # Small deterministic jitter based on siren hash (reproducible across runs)
    siren = str(lead.get("siren") or "0")
    seed  = int(siren[-6:]) if siren.isdigit() else sum(ord(c) for c in siren)
    rng   = random.Random(seed)

    jitter = rng.gauss(0, 0.4)          # std dev = 0.4
    raw    = segment_maturity_score + jitter
    score  = round(max(0.0, min(10.0, raw)), 1)
    gap    = round(10.0 - score, 1)
    level  = _score_to_level(score)

    lead["digital_maturity_score"] = score
    lead["digital_maturity_level"] = level
    lead["digital_gap"]            = gap
    return lead


def build_maturity_overview(segments: list[dict]) -> dict:
    """
    Compute portfolio-level maturity summary for the top-level JSON.

    Returns:
        {
            avg_maturity: float,
            avg_gap: float,
            distribution: {"Faible": int, "Moyen": int, "Élevé": int}
        }
    """
    scores = [s.get("digital_maturity_score") for s in segments if s.get("digital_maturity_score") is not None]
    gaps   = [s.get("digital_gap") for s in segments if s.get("digital_gap") is not None]

    avg_maturity = round(sum(scores) / len(scores), 1) if scores else 0.0
    avg_gap      = round(sum(gaps) / len(gaps), 1)     if gaps   else 0.0

    dist: dict[str, int] = {"Faible": 0, "Moyen": 0, "Élevé": 0}
    for s in segments:
        lvl = s.get("digital_maturity_level")
        if lvl in dist:
            dist[lvl] += 1

    return {
        "avg_maturity": avg_maturity,
        "avg_gap":      avg_gap,
        "distribution": dist,
    }


# ── Private helpers ────────────────────────────────────────────────────────────

def _score_to_level(score: float) -> str:
    """Map a 0–10 score to Faible / Moyen / Élevé."""
    for threshold, label in _LEVEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "Faible"


def _score_to_stage(score: float) -> str:
    """Map a 0–10 score to a 5-stage maturity label."""
    for threshold, stage in _STAGES:
        if score >= threshold:
            return stage
    return "Absent"


def _infer_distribution(
    global_score: float,
    dim_scores: dict[str, float],
) -> dict[str, int]:
    """
    Infer the % distribution of Faible / Moyen / Élevé leads within
    a segment from the global score and dimension variance.

    Logic:
    - We model leads as normally distributed around the global score
      with std dev derived from the spread of dimension scores.
    - P(Faible) = P(score < 5.0), P(Élevé) = P(score >= 8.0), P(Moyen) = remainder.
    - Expressed as integer percentages summing to 100.
    """
    import math

    vals  = list(dim_scores.values())
    spread  = max(vals) - min(vals)
    std_dev = max(0.5, spread * 0.4)   # minimum std=0.5 to avoid degenerate distribution

    def normal_cdf(x: float, mu: float, sigma: float) -> float:
        """Approximate CDF of a normal distribution."""
        return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2))))

    p_faible = normal_cdf(5.0, global_score, std_dev)
    p_eleve  = 1.0 - normal_cdf(8.0, global_score, std_dev)
    p_moyen  = max(0.0, 1.0 - p_faible - p_eleve)

    faible = round(p_faible * 100)
    eleve  = round(p_eleve  * 100)
    moyen  = 100 - faible - eleve     # force sum=100

    # Clamp to valid range
    faible = max(0, min(100, faible))
    eleve  = max(0, min(100, eleve))
    moyen  = max(0, 100 - faible - eleve)

    return {"faible": faible, "moyen": moyen, "eleve": eleve}
