"""
market_analysis/digital_maturity_llm.py
=========================================
Step 4 (optional) of the Hybrid Digital Maturity model.

Generates a Gemini-powered TEXTUAL EXPLANATION for each segment's
digital maturity profile.

CRITICAL CONSTRAINTS:
  - Gemini NEVER generates or overrides the numeric score
  - Gemini produces: description, strengths, weaknesses, opportunity, recommended_pitch
  - Optional bounded score calibration: max ±0.5, only when
    env MATURITY_LLM_CALIBRATION=true (default: false)
  - Full deterministic fallback when Gemini is unavailable

Architecture:
  deterministic baseline + deterministic adjustment = final scores  ← always runs
  LLM explanation = textual context only                            ← runs if key available
  LLM calibration = optional bounded score tweak                    ← disabled by default

Usage:
  from market_analysis.digital_maturity_llm import generate_maturity_analysis
  llm_result = generate_maturity_analysis(segment, export_dir, timestamp)
  # → {
  #     "description": "...",
  #     "strengths": ["...", "..."],
  #     "weaknesses": ["...", "..."],
  #     "opportunity": "...",
  #     "recommended_pitch": "...",
  #     "score_calibration": 0.0   # always 0.0 when calibration is off
  #   }
"""

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Feature flags ──────────────────────────────────────────────────────────────
_API_KEY         = os.environ.get("GEMINI_API_KEY", "")
_LLM_CALIBRATION = os.environ.get("MATURITY_LLM_CALIBRATION", "false").lower() == "true"
_CALIBRATION_MAX = 0.5   # absolute max score delta from LLM calibration

# ── Gemini import ──────────────────────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types as genai_types
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False
    logger.warning("[maturity_llm] google-genai not installed — using rule-based fallback")


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_maturity_analysis(
    segment: dict,
    export_dir: str | None = None,
    timestamp: str | None  = None,
) -> dict:
    """
    Generate a textual maturity explanation for a segment.

    Args:
        segment:    cluster summary dict (must already have digital_maturity_score)
        export_dir: optional path for caching LLM output per run
        timestamp:  run timestamp string for file naming

    Returns:
        dict with keys: description, strengths, weaknesses, opportunity,
                        recommended_pitch, score_calibration
    """
    if _GEMINI_AVAILABLE and _API_KEY:
        result = _call_gemini(segment)
    else:
        result = _rule_based_fallback(segment)

    # Apply score calibration if enabled (bounded to ±_CALIBRATION_MAX)
    if _LLM_CALIBRATION and result.get("score_calibration"):
        delta = float(result["score_calibration"])
        delta = max(-_CALIBRATION_MAX, min(_CALIBRATION_MAX, delta))
        result["score_calibration"] = round(delta, 2)
    else:
        result["score_calibration"] = 0.0

    # Cache to disk if export_dir provided
    if export_dir and timestamp:
        _save_maturity_analysis(segment.get("cluster"), result, export_dir, timestamp)

    return result


def generate_all_maturity_analyses(
    segments: list[dict],
    export_dir: str,
    timestamp: str,
) -> dict[int, dict]:
    """
    Generate maturity LLM analysis for all segments.

    Returns:
        Dict mapping cluster id → llm_analysis dict
    """
    results: dict[int, dict] = {}
    for seg in segments:
        cluster_id = int(seg.get("cluster", 0))
        try:
            results[cluster_id] = generate_maturity_analysis(seg, export_dir, timestamp)
            logger.info(f"[maturity_llm] Generated analysis for cluster {cluster_id}")
        except Exception as exc:
            logger.warning(f"[maturity_llm] Cluster {cluster_id} failed: {exc}")
            results[cluster_id] = _rule_based_fallback(seg)
            results[cluster_id]["score_calibration"] = 0.0
    return results


# ── Gemini call ────────────────────────────────────────────────────────────────

def _call_gemini(segment: dict) -> dict:
    """Call Gemini Flash and parse structured maturity explanation."""
    try:
        client    = genai.Client(api_key=_API_KEY)
        prompt    = _build_prompt(segment)

        response  = client.models.generate_content(
            model    = "gemini-1.5-flash",
            contents = prompt,
            config   = genai_types.GenerateContentConfig(
                response_mime_type = "application/json",
                temperature        = 0.35,
            ),
        )
        raw = response.text.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)
        return _validate_llm_output(data)

    except Exception as exc:
        logger.error(f"[maturity_llm] Gemini call failed: {exc} — using fallback")
        return _rule_based_fallback(segment)


def _build_prompt(segment: dict) -> str:
    """Build the structured prompt for maturity explanation generation."""
    label  = segment.get("label") or segment.get("label_short") or "Segment"
    score  = segment.get("digital_maturity_score", 5.0)
    level  = segment.get("digital_maturity_level", "Moyen")
    gap    = segment.get("digital_gap", 5.0)
    sector = segment.get("secteur_dominant", "Secteur inconnu")
    cat    = segment.get("categorie_dominante", "")
    ca     = _fmt_ca(segment.get("ca_moyen"))
    emp    = segment.get("employes_moyen", "N/A")
    age    = segment.get("age_moyen", "N/A")
    n      = segment.get("n", 0)
    dims   = (segment.get("maturity_details") or {}).get("dimensions") or {}
    reasons = (segment.get("maturity_details") or {}).get("adjustment_reasons") or []

    dim_text = "\n".join(
        f"  - {d.capitalize()}: {v}/10"
        for d, v in dims.items()
    ) if dims else "  Dimensions non disponibles"

    reasons_text = "\n".join(f"  - {r}" for r in reasons[:5]) if reasons else "  Aucun ajustement notable"

    calibration_instruction = (
        """
- "score_calibration": Un float entre -0.5 et +0.5 représentant un ajustement
  suggéré sur le score global basé sur des facteurs sectoriels contextuels que
  les données internes ne capturent pas. 0.0 si aucun ajustement justifié.
"""
        if _LLM_CALIBRATION
        else '- "score_calibration": Toujours 0.0 (calibration désactivée)'
    )

    return f"""Tu es un expert en transformation digitale B2B analysant le profil de maturité numérique d'un segment d'entreprises pour un dashboard CEO.

SEGMENT: {label}
- Leads: {n} entreprises
- Secteur dominant: {sector}
- Catégorie: {cat}
- CA moyen: {ca}
- Effectif moyen: {emp} salariés
- Âge moyen: {age} ans
- Score de maturité digitale: {score}/10 (niveau: {level})
- Écart de transformation: {gap}/10

Scores par dimension:
{dim_text}

Facteurs d'ajustement identifiés:
{reasons_text}

Génère une analyse de maturité digitale UNIQUEMENT en JSON valide, avec exactement cette structure:
{{
  "description": "2-3 phrases expliquant le profil digital de ce segment de façon claire pour un CEO. Inclure le score et le niveau de maturité.",
  "strengths": [
    "Force digitale principale du segment (1 phrase)",
    "Deuxième force identifiée (1 phrase)"
  ],
  "weaknesses": [
    "Principal frein à la transformation digitale (1 phrase)",
    "Deuxième contrainte identifiée (1 phrase)"
  ],
  "opportunity": "1 phrase décrivant la principale opportunité de transformation digitale pour ce segment.",
  "recommended_pitch": "1 phrase de pitch commercial adapté au niveau de maturité de ce segment.",
  {calibration_instruction}
}}

RÈGLES STRICTES:
- Répondre UNIQUEMENT en français
- Ne jamais inventer de chiffres non fournis
- Le champ description doit mentionner le score {score}/10
- Le recommended_pitch doit être actionnable et orienté CEO
- Éviter le jargon technique — rester au niveau décisionnel"""


def _validate_llm_output(data: dict) -> dict:
    """Validate and sanitise Gemini output."""
    def _str(v, default=""):
        return str(v).strip() if v else default

    def _list(v, default_key, default_count=2):
        if isinstance(v, list) and v:
            return [str(x).strip() for x in v[:2]]
        return [f"{default_key} non disponible"] * default_count

    calibration = 0.0
    if _LLM_CALIBRATION:
        try:
            raw_cal = float(data.get("score_calibration", 0))
            calibration = max(-_CALIBRATION_MAX, min(_CALIBRATION_MAX, raw_cal))
        except (TypeError, ValueError):
            calibration = 0.0

    return {
        "description":       _str(data.get("description"), "Analyse non disponible."),
        "strengths":         _list(data.get("strengths"), "Force"),
        "weaknesses":        _list(data.get("weaknesses"), "Frein"),
        "opportunity":       _str(data.get("opportunity"), "Opportunité à analyser."),
        "recommended_pitch": _str(data.get("recommended_pitch"), "Approchezconseil recommandée."),
        "score_calibration": round(calibration, 2),
    }


# ── Deterministic fallback ─────────────────────────────────────────────────────

def _rule_based_fallback(segment: dict) -> dict:
    """
    Generate a rule-based textual explanation when Gemini is unavailable.
    Uses segment stats to produce representative but deterministic text.
    """
    label  = segment.get("label") or segment.get("label_short") or "ce segment"
    score  = segment.get("digital_maturity_score", 5.0)
    level  = segment.get("digital_maturity_level", "Moyen")
    gap    = segment.get("digital_gap", 5.0)
    emp    = _safe_int(segment.get("employes_moyen"))
    ca     = _fmt_ca(segment.get("ca_moyen"))
    age    = _safe_float_str(segment.get("age_moyen"))

    # Description
    if level == "Élevé":
        desc = (
            f"Le segment « {label} » présente un niveau de maturité digitale élevé "
            f"({score}/10), reflétant une adoption avancée des outils numériques. "
            f"Les entreprises de ce groupe disposent généralement d'infrastructures IT "
            f"consolidées et de processus digitaux établis."
        )
        strengths = [
            "Infrastructure technologique solide et gouvernance IT formelle",
            "Processus métier largement digitalisés avec des outils intégrés",
        ]
        weaknesses = [
            "Risque de dette technique sur des systèmes anciens à moderniser",
            "Résistance au changement dans les équipes habituées aux outils existants",
        ]
        opportunity = (
            f"Avec un écart de {gap}/10, ce segment peut accélérer sa transformation "
            f"en ciblant l'IA et l'automatisation avancée."
        )
        pitch = (
            "Proposez une offre d'optimisation et d'accélération — ce segment est prêt "
            "à investir dans la prochaine vague de transformation digitale."
        )
    elif level == "Moyen":
        desc = (
            f"Le segment « {label} » affiche une maturité digitale intermédiaire "
            f"({score}/10), avec des acquis solides dans certaines dimensions "
            f"et des axes de progression significatifs. "
            f"L'écart de {gap}/10 représente un potentiel de transformation concret."
        )
        strengths = [
            "Premiers investissements digitaux réalisés et culture de transformation amorcée",
            "Taille et ressources suffisantes pour absorber de nouveaux outils numériques",
        ]
        weaknesses = [
            "Digitalisation partielle créant des silos entre systèmes anciens et nouveaux",
            "Manque de gouvernance data limitant l'exploitation des données disponibles",
        ]
        opportunity = (
            f"Un programme de digitalisation ciblé peut réduire l'écart de {gap}/10 "
            f"et créer un avantage concurrentiel rapide."
        )
        pitch = (
            "Proposez une roadmap de transformation en 3 étapes — ce segment a la "
            "maturité pour avancer mais a besoin d'un cadre structuré."
        )
    else:  # Faible
        desc = (
            f"Le segment « {label} » présente un niveau de maturité digitale faible "
            f"({score}/10), indiquant un fort potentiel de transformation. "
            f"L'écart de {gap}/10 représente une opportunité commerciale majeure "
            f"pour accompagner ces entreprises dans leur parcours numérique."
        )
        strengths = [
            "Fort potentiel de transformation — chaque investissement digital génère un ROI élevé",
            "Marge de progression importante sur toutes les dimensions numériques",
        ]
        weaknesses = [
            "Infrastructure digitale limitée nécessitant des investissements fondamentaux",
            "Culture digitale à développer — accompagnement humain indispensable",
        ]
        opportunity = (
            f"Avec un écart de {gap}/10, ce segment représente l'opportunité de "
            f"transformation la plus importante du portefeuille."
        )
        pitch = (
            "Positionnez-vous comme partenaire de transformation de bout en bout — "
            "ce segment a besoin d'un accompagnement global, pas d'une solution unique."
        )

    return {
        "description":       desc,
        "strengths":         strengths,
        "weaknesses":        weaknesses,
        "opportunity":       opportunity,
        "recommended_pitch": pitch,
        "score_calibration": 0.0,
    }


# ── File I/O ───────────────────────────────────────────────────────────────────

def _save_maturity_analysis(
    cluster_id: int | None,
    analysis: dict,
    export_dir: str,
    timestamp: str,
) -> None:
    """Cache individual maturity analysis to disk (optional)."""
    try:
        path = Path(export_dir) / "maturity"
        path.mkdir(parents=True, exist_ok=True)
        cid = cluster_id if cluster_id is not None else "unknown"
        fname = path / f"maturity_analysis_c{cid}_{timestamp}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "source": "gemini-1.5-flash" if (_GEMINI_AVAILABLE and _API_KEY) else "rule-based",
                "cluster": cluster_id,
                "analysis": analysis,
            }, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.warning(f"[maturity_llm] Could not save analysis for cluster {cluster_id}: {exc}")


# ── Formatting helpers ─────────────────────────────────────────────────────────

def _fmt_ca(v) -> str:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "N/A"
    if v >= 1e9: return f"{v/1e9:.1f} Md€"
    if v >= 1e6: return f"{v/1e6:.0f} M€"
    if v >= 1e3: return f"{v/1e3:.0f} k€"
    return f"{v:.0f} €"

def _safe_int(v) -> str:
    try: return str(int(float(v)))
    except (TypeError, ValueError): return "N/A"

def _safe_float_str(v) -> str:
    try: return f"{float(v):.0f}"
    except (TypeError, ValueError): return "N/A"
