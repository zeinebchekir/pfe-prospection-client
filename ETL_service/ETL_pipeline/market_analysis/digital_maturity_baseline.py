"""
market_analysis/digital_maturity_baseline.py
============================================
Step 1 of the Hybrid Digital Maturity model.

Provides a deterministic sector-level baseline score for each of the
5 maturity dimensions. Values represent the EXPECTED digital maturity
for a typical company in that French B2B sector (scale 0–10).

Sources of calibration:
  - France Num (2022-2024 barometer)
  - McKinsey / Wavestone B2B sector benchmarks adapted for French market
  - Qualifix domain expertise

Architecture:
  final_score = baseline + adjustment (+ optional LLM delta, bounded)
  This file covers ONLY the baseline layer.

Usage:
  from market_analysis.digital_maturity_baseline import get_sector_baseline
  baseline = get_sector_baseline("Transport d'électricité")
  # → {"tech": 5.5, "data": 4.8, "process": 6.0, "culture": 5.0, "cx": 4.5}
"""

from __future__ import annotations

# ── Dimension keys ────────────────────────────────────────────────────────────
DIMENSIONS = ("tech", "data", "process", "culture", "cx")

# ── Generic fallback (unknown or Autre sector) ────────────────────────────────
_FALLBACK: dict[str, float] = {
    "tech":    5.0,
    "data":    5.0,
    "process": 5.0,
    "culture": 5.0,
    "cx":      5.0,
}

# ── Sector baseline table ─────────────────────────────────────────────────────
# Keys are lowercased partial sector strings (substring matching).
# Values: {tech, data, process, culture, cx} on a 0–10 scale.
# Higher = more digitally mature by default in that sector.
#
# CEO-readable rationale for each sector listed inline.

_SECTOR_TABLE: list[tuple[str, dict[str, float]]] = [
    # ── Energy & Utilities ────────────────────────────────────────────────────
    # High process (SCADA, IoT); moderate data analytics; low CX digital.
    ("transport d'électricité", {"tech": 6.5, "data": 5.5, "process": 7.0, "culture": 5.5, "cx": 4.5}),
    ("production d'électricité", {"tech": 6.5, "data": 5.5, "process": 7.0, "culture": 5.5, "cx": 4.5}),
    ("distribution d'énergie",   {"tech": 6.0, "data": 5.0, "process": 6.5, "culture": 5.0, "cx": 4.0}),
    ("collecte de déchets",      {"tech": 4.5, "data": 4.0, "process": 5.5, "culture": 4.0, "cx": 3.5}),
    ("eau et assainissement",    {"tech": 4.5, "data": 4.5, "process": 5.5, "culture": 4.0, "cx": 3.5}),

    # ── Transport & Logistics ─────────────────────────────────────────────────
    # Track-and-trace maturity; strong process but lagging data/culture.
    ("transport de voyageurs", {"tech": 5.5, "data": 5.0, "process": 6.0, "culture": 5.0, "cx": 5.5}),
    ("transport de marchandises", {"tech": 5.0, "data": 4.5, "process": 6.0, "culture": 4.5, "cx": 4.0}),
    ("logistique",             {"tech": 5.5, "data": 5.5, "process": 6.5, "culture": 5.0, "cx": 4.5}),

    # ── Public Services ───────────────────────────────────────────────────────
    # Historically low; digitisation is picking up via "France Numérique" programs.
    ("services publics",  {"tech": 4.0, "data": 3.5, "process": 4.5, "culture": 3.5, "cx": 4.0}),
    ("administration",    {"tech": 3.5, "data": 3.5, "process": 4.0, "culture": 3.0, "cx": 3.5}),
    ("collectivité",      {"tech": 3.5, "data": 3.5, "process": 4.0, "culture": 3.0, "cx": 3.5}),
    ("enseignement",      {"tech": 4.5, "data": 4.0, "process": 4.5, "culture": 4.5, "cx": 4.5}),
    ("recherche",         {"tech": 6.0, "data": 6.5, "process": 5.0, "culture": 6.0, "cx": 4.0}),
    ("santé",             {"tech": 5.5, "data": 5.5, "process": 5.5, "culture": 5.0, "cx": 5.0}),
    ("hôpital",           {"tech": 5.0, "data": 5.0, "process": 5.5, "culture": 4.5, "cx": 4.5}),

    # ── Wholesale & Distribution ──────────────────────────────────────────────
    # Commerce de gros: legacy ERP systems; moderate tech; low CX.
    ("commerce de gros",  {"tech": 5.0, "data": 5.0, "process": 5.5, "culture": 4.5, "cx": 4.0}),
    ("négoce",            {"tech": 5.0, "data": 5.0, "process": 5.5, "culture": 4.5, "cx": 4.0}),

    # ── Retail ───────────────────────────────────────────────────────────────
    # Omnichannel driven; high CX scores; strong data analytics.
    ("commerce de détail", {"tech": 5.5, "data": 5.5, "process": 5.5, "culture": 5.0, "cx": 6.5}),
    ("grande distribution", {"tech": 6.0, "data": 6.0, "process": 6.0, "culture": 5.5, "cx": 7.0}),
    ("e-commerce",         {"tech": 7.5, "data": 7.0, "process": 6.5, "culture": 7.0, "cx": 8.0}),

    # ── Industry & Manufacturing ──────────────────────────────────────────────
    # Industry 4.0 adoption variable; process automation high in large plants.
    ("industrie",          {"tech": 5.5, "data": 5.0, "process": 6.0, "culture": 4.5, "cx": 4.0}),
    ("fabrication",        {"tech": 5.5, "data": 5.0, "process": 6.0, "culture": 4.5, "cx": 4.0}),
    ("métallurgie",        {"tech": 5.0, "data": 4.5, "process": 5.5, "culture": 4.0, "cx": 3.5}),
    ("automobile",         {"tech": 7.0, "data": 6.5, "process": 7.5, "culture": 6.0, "cx": 5.5}),
    ("aérospatial",        {"tech": 8.0, "data": 7.5, "process": 8.0, "culture": 7.0, "cx": 5.5}),
    ("défense",            {"tech": 7.0, "data": 6.5, "process": 7.5, "culture": 6.0, "cx": 4.0}),
    ("chimie",             {"tech": 6.0, "data": 6.0, "process": 6.5, "culture": 5.5, "cx": 4.5}),

    # ── Construction & Real Estate ────────────────────────────────────────────
    # Slow digitisation; BIM adoption rising but not widespread.
    ("construction",        {"tech": 4.0, "data": 3.5, "process": 4.5, "culture": 3.5, "cx": 3.5}),
    ("bâtiment",            {"tech": 4.0, "data": 3.5, "process": 4.5, "culture": 3.5, "cx": 3.5}),
    ("immobilier",          {"tech": 4.5, "data": 4.5, "process": 4.5, "culture": 4.0, "cx": 5.0}),
    ("location immobilière",{"tech": 4.0, "data": 4.0, "process": 4.5, "culture": 3.5, "cx": 4.5}),

    # ── Financial Services ────────────────────────────────────────────────────
    # Highest digital maturity overall; fintechs skew the average up.
    ("banque",              {"tech": 8.0, "data": 8.0, "process": 7.5, "culture": 7.0, "cx": 8.0}),
    ("assurance",           {"tech": 7.5, "data": 7.5, "process": 7.0, "culture": 6.5, "cx": 7.5}),
    ("finance",             {"tech": 7.5, "data": 7.5, "process": 7.0, "culture": 6.5, "cx": 7.5}),

    # ── Technology & IT ───────────────────────────────────────────────────────
    ("informatique",        {"tech": 9.0, "data": 8.5, "process": 8.0, "culture": 8.5, "cx": 8.0}),
    ("télécommunications",  {"tech": 8.5, "data": 8.0, "process": 7.5, "culture": 7.5, "cx": 8.0}),
    ("numérique",           {"tech": 9.0, "data": 8.5, "process": 8.0, "culture": 8.5, "cx": 8.0}),
    ("logiciel",            {"tech": 9.0, "data": 8.5, "process": 8.0, "culture": 8.5, "cx": 8.0}),

    # ── Professional Services ─────────────────────────────────────────────────
    ("conseil",             {"tech": 6.5, "data": 6.5, "process": 6.0, "culture": 6.5, "cx": 6.0}),
    ("audit",               {"tech": 6.5, "data": 7.0, "process": 6.5, "culture": 6.0, "cx": 5.5}),
    ("juridique",           {"tech": 5.5, "data": 5.5, "process": 5.5, "culture": 5.0, "cx": 5.0}),
    ("ressources humaines", {"tech": 6.0, "data": 6.0, "process": 5.5, "culture": 6.0, "cx": 5.5}),
    ("marketing",           {"tech": 7.0, "data": 7.5, "process": 6.0, "culture": 7.0, "cx": 8.0}),

    # ── Agriculture & Food ────────────────────────────────────────────────────
    ("agriculture",         {"tech": 4.0, "data": 4.0, "process": 4.5, "culture": 3.5, "cx": 3.5}),
    ("agroalimentaire",     {"tech": 5.0, "data": 5.0, "process": 5.5, "culture": 4.5, "cx": 5.0}),
    ("restauration",        {"tech": 4.5, "data": 4.0, "process": 4.5, "culture": 4.0, "cx": 5.5}),

    # ── Inspections / Certification ───────────────────────────────────────────
    # Technical/regulatory sector; decent process automation, moderate tech.
    ("inspections techniques", {"tech": 5.5, "data": 5.0, "process": 6.0, "culture": 5.0, "cx": 4.5}),
    ("certification",          {"tech": 5.5, "data": 5.5, "process": 6.0, "culture": 5.0, "cx": 5.0}),

    # ── Catch-all: Autre ─────────────────────────────────────────────────────
    ("autre", _FALLBACK.copy()),
]


# ── Public API ─────────────────────────────────────────────────────────────────

def get_sector_baseline(sector: str) -> dict[str, float]:
    """
    Return the baseline maturity scores {tech, data, process, culture, cx}
    for a given sector string (case-insensitive substring match).

    Falls back to neutral 5.0 across all dimensions if no match found.

    Args:
        sector: sector string from DB (e.g. "Transport d'électricité")

    Returns:
        dict with keys: tech, data, process, culture, cx — float values 0–10
    """
    if not sector:
        return _FALLBACK.copy()

    sector_lower = sector.lower()

    for keyword, scores in _SECTOR_TABLE:
        if keyword in sector_lower:
            return dict(scores)   # defensive copy

    # No match — return neutral fallback
    return _FALLBACK.copy()


def list_covered_sectors() -> list[str]:
    """Return all keyword strings currently covered (for documentation / tests)."""
    return [kw for kw, _ in _SECTOR_TABLE]
