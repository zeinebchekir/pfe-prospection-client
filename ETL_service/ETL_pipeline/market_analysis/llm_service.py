"""
market_analysis/llm_service.py
===============================
Gemini-powered dynamic insight generation for the CEO dashboard.

Input:  cluster_summary data (segments list + validation metrics)
Output: structured JSON with 6 executive insights

Requires env var: GEMINI_API_KEY
Writes:  cluster_insights.json  (latest)
         cluster_insights_YYYYMMDD_HHMM.json  (versioned)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from market_analysis.text_utils import fix_mojibake, repair_text_payload

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types as genai_types

    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False
    logger.warning(
        "[llm_service] google-genai not installed. Falling back to rule-based insights."
    )

_API_KEY = os.environ.get("GEMINI_API_KEY", "")

_FALLBACK_INSIGHTS = [
    {
        "title": "Concentration du portefeuille",
        "description": "Le segment dominant représente la majorité du potentiel CA. Prioriser les actions commerciales sur ce profil.",
        "priority": "high",
        "icon": "TrendingUp",
    },
    {
        "title": "Opportunité scale",
        "description": "Les segments volumétriques (nombreux leads, CA modéré) sont idéaux pour une approche self-serve automatisée.",
        "priority": "medium",
        "icon": "Zap",
    },
    {
        "title": "Segments à haut CA individuel",
        "description": "Quelques segments concentrent un CA moyen très élevé. Investir en équipe dédiée grand compte est justifié.",
        "priority": "high",
        "icon": "Target",
    },
    {
        "title": "Diversification géographique",
        "description": "La concentration Île-de-France est forte. Identifier des opportunités dans d'autres régions pour réduire le risque.",
        "priority": "medium",
        "icon": "MapPin",
    },
    {
        "title": "Ancienneté comme signal de fidélité",
        "description": "Les entreprises établies depuis plus de 40 ans ont des cycles de décision longs mais sont plus fidèles client.",
        "priority": "low",
        "icon": "Clock",
    },
    {
        "title": "Re-run recommandé",
        "description": "Relancez l'analyse après chaque import ETL majeur pour maintenir la segmentation à jour.",
        "priority": "low",
        "icon": "RefreshCw",
    },
]


def generate_insights(
    segments: list[dict],
    validation: dict,
    export_dir: str,
    timestamp: str,
) -> list[dict]:
    """Generate executive insights via Gemini LLM or fall back to rule-based insights."""
    insights = (
        _call_gemini(segments, validation)
        if _GEMINI_AVAILABLE and _API_KEY
        else _FALLBACK_INSIGHTS
    )
    insights = repair_text_payload(insights)
    _save_insights(insights, export_dir, timestamp)
    return insights


def _call_gemini(segments: list[dict], validation: dict) -> list[dict]:
    """Call Gemini and return structured insights."""
    try:
        client = genai.Client(api_key=_API_KEY)
        prompt = _build_prompt(segments, validation)

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
            ),
        )
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)
        insights = data.get("insights", data) if isinstance(data, dict) else data
        if not isinstance(insights, list):
            raise ValueError("Unexpected Gemini response format")

        icon_map = {"high": "TrendingUp", "medium": "Target", "low": "Info"}
        result = []
        for item in insights[:6]:
            priority = str(item.get("priority", "medium")).lower()
            result.append(
                {
                    "title": fix_mojibake(str(item.get("title", "Insight"))),
                    "description": fix_mojibake(str(item.get("description", ""))),
                    "priority": priority,
                    "icon": str(item.get("icon", icon_map.get(priority, "Info"))),
                }
            )
        logger.info("[llm_service] Gemini returned %s insights", len(result))
        return result

    except Exception as exc:
        logger.error(
            "[llm_service] Gemini call failed: %s. Using fallback insights.", exc
        )
        return _FALLBACK_INSIGHTS


def _build_prompt(segments: list[dict], validation: dict) -> str:
    """Build the Gemini prompt from segment statistics."""

    def fmt(value):
        if value is None:
            return "N/A"
        if value >= 1e9:
            return f"{value/1e9:.1f} Md€"
        if value >= 1e6:
            return f"{value/1e6:.1f} M€"
        if value >= 1e3:
            return f"{value/1e3:.0f} k€"
        return f"{round(value, 0):.0f} €"

    seg_lines = []
    for segment in segments:
        seg_lines.append(
            f"- {segment['label']} (C{segment['cluster']}): {segment['n']} leads, "
            f"CA moyen {fmt(segment.get('ca_moyen'))}, "
            f"effectif moyen {segment.get('employes_moyen', 'N/A')}, "
            f"âge moyen {segment.get('age_moyen', 'N/A')} ans, "
            f"région dominante: {segment.get('region_dominante', 'N/A')}, "
            f"secteur: {segment.get('secteur_dominant', 'N/A')}"
        )

    model_type = validation.get("model_type", "kmeans")
    if model_type == "decision_tree":
        model_context = f"""The database has been segmented into {len(segments)} business segments using a supervised Decision Tree classifier.
Training accuracy: {validation.get('training_accuracy', 'N/A')}
Tree depth: {validation.get('tree_depth', 'N/A')}
Number of leaves: {validation.get('n_leaves', 'N/A')}"""
    else:
        silhouette = validation.get("silhouette", "N/A")
        silhouette_interp = validation.get("silhouette_interpretation", "")
        best_k = (validation.get("elbow") or {}).get("best_k", "N/A")
        model_context = f"""The database has been segmented into {len(segments)} clusters using KMeans clustering.
Silhouette score: {silhouette} ({silhouette_interp})
Recommended K from elbow analysis: {best_k}"""

    return f"""You are an expert B2B sales strategy consultant analyzing a CRM lead database for a CEO.

{model_context}

Segment profiles:
{chr(10).join(seg_lines)}

Generate exactly 6 executive insights in FRENCH focusing on:
1. Highest revenue opportunity (which segment to prioritize)
2. Segmentation quality and what it means
3. Sales strategy recommendations (which approach per segment type)
4. Scale / automation opportunity (high volume segments)
5. Geographic or sector concentration risk
6. One anomaly or unexpected finding

Respond ONLY with valid JSON in this exact format:
{{
  "insights": [
    {{
      "title": "Titre court (max 8 mots)",
      "description": "Explication claire pour un CEO (2-3 phrases). Chiffres précis inclus.",
      "priority": "high|medium|low",
      "icon": "TrendingUp|Target|Zap|AlertTriangle|MapPin|Users|BarChart3|RefreshCw|Lightbulb|Clock"
    }}
  ]
}}"""


def _save_insights(insights: list[dict], export_dir: str, timestamp: str) -> None:
    path = Path(export_dir)
    path.mkdir(parents=True, exist_ok=True)

    payload = repair_text_payload(
        {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": (
                "gemini-1.5-flash"
                if (_GEMINI_AVAILABLE and _API_KEY)
                else "rule-based-fallback"
            ),
            "insights": insights,
        }
    )

    versioned = path / f"cluster_insights_{timestamp}.json"
    with open(versioned, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, default=str)

    latest = path / "cluster_insights.json"
    with open(latest, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, default=str)

    logger.info("[llm_service] Insights saved -> %s", versioned)


def load_insights(export_dir: str) -> list[dict]:
    """Load latest cluster_insights.json, return an empty list if missing."""
    path = Path(export_dir) / "cluster_insights.json"
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        repaired = repair_text_payload(data)
        return repaired.get("insights", [])
    except Exception:
        return []
