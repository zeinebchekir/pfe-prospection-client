"""
Decision-tree segmentation engine.

This module replaces the previous KMeans implementation while preserving the
existing FastAPI endpoints and JSON contract expected by the frontend.

Beginner-friendly mental model:
1. Load companies from the database.
2. Clean the raw fields and create ML/business features.
3. Create rule-based segment labels such as PME_Small_IT or ETI_Large.
4. Train a shallow Decision Tree to reproduce those business labels.
5. Predict a segment for every company.
6. Build summaries, drilldowns, maturity analysis, insights, and JSON files
   consumed by the Vue dashboard.

Important naming note:
The JSON still uses words like "cluster" and filenames like
cluster_summary.json because the old frontend expects them. In v4, those
"cluster" values are actually decision-tree business segment ids.
"""

from __future__ import annotations

import json
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sqlalchemy.orm import Session

from market_analysis.digital_maturity import (
    build_maturity_overview,
    compute_lead_maturity,
    compute_maturity,
)
from market_analysis.digital_maturity_llm import generate_all_maturity_analyses
from market_analysis.explainability import compute_explainability
from market_analysis.llm_service import generate_insights
from market_analysis.validation import compute_decision_tree_validation

warnings.filterwarnings("ignore")

# Directory where the latest and versioned JSON exports are written.
# The environment variable lets Docker/production override the default path.
DEFAULT_EXPORT_DIR = os.environ.get(
    "SEGMENTATION_EXPORT_DIR", "/opt/airflow/exports/segmentation"
)

# Metadata stored in cluster_summary.json so the frontend/docs know
# which segmentation engine produced the current results.
MODEL_TYPE = "decision_tree"

# Numeric feature columns used by scikit-learn.
# The Decision Tree cannot read raw text, so category/sector/band are encoded
# into integers before training.
TREE_FEATURE_COLUMNS = ["cat_enc", "ca", "sec_enc", "band_enc"]
TREE_FEATURE_DISPLAY_NAMES = ["Categorie", "CA (€)", "Secteur", "CA Band"]

# Converts French employee-size ranges from the database into approximate
# numeric midpoints. Example: "100 à 199 salariés" becomes 149.
# This numeric value is used for statistics, explainability, and drilldowns.
EFFECTIF_MAP = {
    "Unité non employeuse (0 salarié)": 0,
    "0 salarié": 0,
    "1 à 2 salariés": 1,
    "3 à 5 salariés": 4,
    "6 à 9 salariés": 7,
    "10 à 19 salariés": 14,
    "20 à 49 salariés": 34,
    "50 à 99 salariés": 74,
    "100 à 199 salariés": 149,
    "200 à 249 salariés": 224,
    "250 à 499 salariés": 374,
    "500 à 999 salariés": 749,
    "1 000 à 1 999 salariés": 1499,
    "2 000 à 4 999 salariés": 3499,
    "5 000 à 9 999 salariés": 7499,
    "10 000 salariés et plus": 15000,
}

# Groups detailed sector labels into broader macro sectors.
# This makes the segmentation rules easier to understand than using hundreds
# of raw sector names. Unknown sectors become "Other".
SECTOR_MAP = {
    "Commerce de gros": "Commerce",
    "62.02A": "IT",
    "Commerce de gros de bois et de matériaux de construction": "Commerce",
    "Conseil informatique": "IT",
    "Commerce de gros de machines-outils": "Commerce",
    "Autres activités informatiques": "IT",
    "Act. auxil. assurance": "Finance",
    "Tierce mainten. syst.": "IT",
    "Traitement de données, hébergement et activités connexes": "IT",
    "Autres activités d'enseignement": "Services",
    "Services de prérogative publique": "Public",
    "Activités des organisations professionnelles'": "Services",
    "Collecte, gestion déchets": "Services",
    "Activité des médecins et des dentistes": "Services",
    "Location de logements": "Services",
}

# Stable list of possible decision-tree business segments.
# Keeping a fixed order helps keep ids, colors, and frontend display stable.
SEGMENT_ORDER = [
    "PME_Small_IT",
    "PME_Small_NonIT",
    "PME_Mid",
    "ETI_IT",
    "ETI_Mid",
    "ETI_Large",
    "GE_Large",
]

# Human-readable metadata for every segment.
# "cluster" is kept for frontend compatibility, but it now means segment id.
# The label/color/recommendation fields are displayed by the Vue dashboard.
SEGMENT_META = {
    "PME_Small_IT": {
        "cluster": 0,
        "label": "PME technologiques",
        "label_short": "PME",
        "label_sub": "Petits acteurs IT",
        "color": "#04ADBF",
        "recommendation": "Offre digitale packagée",
    },
    "PME_Small_NonIT": {
        "cluster": 1,
        "label": "PME opérationnelles",
        "label_short": "PME",
        "label_sub": "Petits acteurs non-IT",
        "color": "#56A632",
        "recommendation": "Accompagnement progressif",
    },
    "PME_Mid": {
        "cluster": 2,
        "label": "PME en croissance",
        "label_short": "PME",
        "label_sub": "CA intermédiaire",
        "color": "#F29F05",
        "recommendation": "Montee en gamme structuree",
    },
    "ETI_IT": {
        "cluster": 3,
        "label": "ETI technologiques",
        "label_short": "ETI",
        "label_sub": "Orientees IT",
        "color": "#303E8C",
        "recommendation": "Co-innovation et integration",
    },
    "ETI_Mid": {
        "cluster": 4,
        "label": "ETI etablies",
        "label_short": "ETI",
        "label_sub": "CA intermediaire",
        "color": "#2D3773",
        "recommendation": "Relationship selling",
    },
    "ETI_Large": {
        "cluster": 5,
        "label": "ETI grands comptes",
        "label_short": "ETI",
        "label_sub": "CA eleve",
        "color": "#C2410C",
        "recommendation": "ABM et equipe dediee",
    },
    "GE_Large": {
        "cluster": 6,
        "label": "Grands groupes",
        "label_short": "GE",
        "label_sub": "Enterprise",
        "color": "#8E1C1C",
        "recommendation": "Vente enterprise executive",
    },
}

# Fields copied when exporting a company row into JSON drilldowns/top lists.
# Keeping the list centralized avoids forgetting fields in helper functions.
COMPANY_EXPORT_FIELDS = [
    "siren",
    "nom_entreprise",
    "ville",
    "secteur_activite",
    "categorie_entreprise",
    "tranche_effectif",
    "chiffre_affaires",
    "age_entreprise",
    "region",
    "cluster",
    "nb_employes_mid",
    "nb_locaux",
    "macro_sector",
    "ca_band",
    "decision_tree_confidence",
    "segment_rule",
]



# Convert raw revenue/CA into a business-friendly band.
# This is one of the core features used by the segmentation rules and tree.
# Missing CA is kept as "Unknown" instead of crashing the pipeline.
def ca_band(ca: Any) -> str:
    if pd.isna(ca):
        return "Unknown"
    if ca < 10_000_000:
        return "Small"
    if ca < 50_000_000:
        return "Mid"
    return "Large"



# Convert a detailed sector label into a broader macro sector.
# Example: "Conseil informatique" becomes "IT".
# Anything not present in SECTOR_MAP becomes "Other".
def macro_sector(sector_label: Any) -> str:
    return SECTOR_MAP.get(sector_label, "Other")



# Standardize company category names before applying business rules.
# The database can contain slightly different labels such as PME, ETI,
# Grande Entreprise, micro, etc. This function normalizes them.
def normalize_company_category(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "Petite et Moyenne Entreprise"

    lower = text.lower()
    if "grande" in lower:
        return "Grande Entreprise"
    if "interm" in lower or lower == "eti":
        return "Entreprise de Taille Intermédiaire"
    if (
        "pme" in lower
        or "petite" in lower
        or "moyenne" in lower
        or "micro" in lower
    ):
        return "Petite et Moyenne Entreprise"
    return text



# Apply the first deterministic business segmentation layer.
# This creates the target label that the Decision Tree will learn.
# In simple terms: category + CA band + macro sector -> segment code.
def segment_label(row: pd.Series) -> str | None:
    category = normalize_company_category(row.get("categorie_entreprise"))
    band = ca_band(row.get("ca"))
    sector = macro_sector(row.get("secteur_activite"))

    if category == "Petite et Moyenne Entreprise":
        if band == "Small":
            return "PME_Small_IT" if sector == "IT" else "PME_Small_NonIT"
        return "PME_Mid"

    if category == "Entreprise de Taille Intermédiaire":
        if sector == "IT":
            return "ETI_IT"
        if band == "Large":
            return "ETI_Large"
        return "ETI_Mid"

    if category == "Grande Entreprise":
        return "GE_Large"

    return None



# Convert a postal code into a coarse French region used for dashboard stats.
# This is not used directly by the Decision Tree, but it is useful for
# segment summaries, dominant dimensions, and frontend filters.
def _get_region(cp: Any) -> str:
    try:
        dept = int(str(cp)) // 1000
        if 75 <= dept <= 95:
            return "Ile-de-France"
        if dept <= 30:
            return "Sud"
        if dept <= 55:
            return "Est"
        if dept <= 76:
            return "Nord-Ouest"
        return "Autre"
    except Exception:
        return "Inconnu"



# Return the most frequent non-null value in a pandas Series.
# Used to find the dominant category/sector/region of a segment.
# If the series is empty, return a safe default.
def _safe_mode(series: pd.Series, default: str = "Inconnu") -> str:
    mode_vals = series.mode(dropna=True)
    if len(mode_vals) > 0:
        return str(mode_vals.iloc[0])
    return default



# Convert pandas/numpy values into normal Python values before JSON export.
# This prevents json.dump from failing on np.int64, np.float64, timestamps,
# or NaN-like values.
def _json_safe(value: Any) -> Any:
    if isinstance(value, (np.floating,)):
        return None if pd.isna(value) else float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value



# Convert one pandas row into a JSON-ready company dictionary.
# This helper is reused by drilldowns, top lists, extreme cases, and
# representative-company exports.
def _to_row(
    row: pd.Series,
    label_map: dict[int, str],
    mat_score_map: dict[int, float],
    mat_level_map: dict[int, str],
) -> dict[str, Any]:
    cluster_id = int(row.get("cluster", -1))
    payload: dict[str, Any] = {}
    for field in COMPANY_EXPORT_FIELDS:
        value = row.get(field)
        if pd.isna(value) if isinstance(value, float) else False:
            payload[field] = None
        else:
            payload[field] = _json_safe(value.item() if hasattr(value, "item") else value)
    payload["cluster_label"] = label_map.get(cluster_id, f"Cluster {cluster_id}")
    payload["digital_maturity_score"] = mat_score_map.get(cluster_id)
    payload["digital_maturity_level"] = mat_level_map.get(cluster_id)
    payload["digital_gap"] = None
    return payload



# Compute a small statistics block for a numeric column.
# The frontend uses these values in the segment detail modal: mean, median,
# min, max, and standard deviation.
def _stat_block(series: pd.Series) -> dict[str, float | None]:
    clean = series.dropna()
    if clean.empty:
        return {"mean": None, "median": None, "min": None, "max": None, "std": None}
    return {
        "mean": round(float(clean.mean()), 2),
        "median": round(float(clean.median()), 2),
        "min": round(float(clean.min()), 2),
        "max": round(float(clean.max()), 2),
        "std": round(float(clean.std()), 2),
    }



# Compute the coefficient of variation: std / mean.
# It measures dispersion inside a segment. A high value means the segment is
# heterogeneous, so averages may be misleading.
def _safe_cv(series: pd.Series) -> float | None:
    clean = series.dropna()
    if clean.empty:
        return None
    mean = clean.mean()
    if abs(mean) < 1e-9:
        return None
    return round(float(clean.std() / abs(mean)), 4)



# Compare a segment average against the global portfolio average.
# Example: -41.2 means the segment mean is 41.2% below the global mean.
def _pct_delta(cluster_mean: float | None, global_mean: float | None) -> float | None:
    if cluster_mean is None or global_mean is None:
        return None
    if abs(global_mean) < 1e-9:
        return None
    return round((cluster_mean - global_mean) / abs(global_mean) * 100, 2)



# Return the top or bottom N company rows for a given numeric column.
# Used for rankings such as Top CA, Bottom CA, Top Effectif, and Oldest.
def _top_rows(
    frame: pd.DataFrame,
    column: str,
    n: int,
    ascending: bool,
    label_map: dict[int, str],
    mat_score_map: dict[int, float],
    mat_level_map: dict[int, str],
) -> list[dict[str, Any]]:
    sorted_rows = frame.dropna(subset=[column]).sort_values(column, ascending=ascending)
    return [
        _to_row(row, label_map, mat_score_map, mat_level_map)
        for _, row in sorted_rows.head(n).iterrows()
    ]



# Return a single extreme company row for a numeric column.
# Example: highest revenue company, youngest company, or smallest employee count.
def _extreme_row(
    frame: pd.DataFrame,
    column: str,
    ascending: bool,
    label_map: dict[int, str],
    mat_score_map: dict[int, float],
    mat_level_map: dict[int, str],
) -> dict[str, Any] | None:
    sorted_rows = frame.dropna(subset=[column]).sort_values(column, ascending=ascending)
    if sorted_rows.empty:
        return None
    return _to_row(sorted_rows.iloc[0], label_map, mat_score_map, mat_level_map)



# Select companies that best represent a segment.
# The logic prefers high decision-tree confidence, closeness to segment medians,
# and then higher revenue as a tie-breaker.
def _representative_companies(
    frame: pd.DataFrame,
    n: int,
    label_map: dict[int, str],
    mat_score_map: dict[int, float],
    mat_level_map: dict[int, str],
) -> list[dict[str, Any]]:
    if frame.empty:
        return []

    numeric_cols = ["ca_for_model", "nb_employes_mid", "nb_locaux", "age_entreprise"]
    medians = frame[numeric_cols].median().fillna(0)
    scales = frame[numeric_cols].std().replace(0, 1).fillna(1)

    ranked = frame.copy()
    ranked["_distance"] = 0.0
    for column in numeric_cols:
        ranked["_distance"] += (
            (ranked[column].fillna(medians[column]) - medians[column]).abs() / scales[column]
        )

    ranked = ranked.sort_values(
        ["decision_tree_confidence", "_distance", "ca_for_model"],
        ascending=[False, True, False],
    )

    return [
        _to_row(row, label_map, mat_score_map, mat_level_map)
        for _, row in ranked.head(n).iterrows()
    ]



# Build the detailed drilldown object for one segment.
# This powers the modal/expanded UI: stats, dominant dimensions, extremes,
# representative companies, rankings, global comparison, and homogeneity.
def _build_drilldown(
    cluster_id: int,
    clustered_frame: pd.DataFrame,
    label_map: dict[int, str],
    mat_score_map: dict[int, float],
    mat_level_map: dict[int, str],
) -> dict[str, Any]:
    subset = clustered_frame[clustered_frame["cluster"] == cluster_id].copy()

    ca_stats = _stat_block(subset["chiffre_affaires"])
    eff_stats = _stat_block(subset["nb_employes_mid"])
    age_stats = _stat_block(subset["age_entreprise"])
    loc_stats = _stat_block(subset["nb_locaux"])

    dominant = {
        "categorie_entreprise": _safe_mode(subset["categorie_entreprise"], "PME"),
        "secteur_activite": _safe_mode(subset["secteur_activite"], "Inconnu"),
        "region": _safe_mode(subset["region"], "Inconnu"),
    }

    common_kwargs = {
        "label_map": label_map,
        "mat_score_map": mat_score_map,
        "mat_level_map": mat_level_map,
    }
    extremes = {
        "lowest_ca": _extreme_row(subset, "chiffre_affaires", True, **common_kwargs),
        "highest_ca": _extreme_row(subset, "chiffre_affaires", False, **common_kwargs),
        "lowest_effectif": _extreme_row(subset, "nb_employes_mid", True, **common_kwargs),
        "highest_effectif": _extreme_row(subset, "nb_employes_mid", False, **common_kwargs),
        "youngest_company": _extreme_row(subset, "age_entreprise", True, **common_kwargs),
        "oldest_company": _extreme_row(subset, "age_entreprise", False, **common_kwargs),
    }

    top_lists = {
        "top_ca": _top_rows(subset, "chiffre_affaires", 10, False, **common_kwargs),
        "bottom_ca": _top_rows(subset, "chiffre_affaires", 10, True, **common_kwargs),
        "top_effectif": _top_rows(subset, "nb_employes_mid", 10, False, **common_kwargs),
        "bottom_effectif": _top_rows(subset, "nb_employes_mid", 10, True, **common_kwargs),
        "oldest": _top_rows(subset, "age_entreprise", 10, False, **common_kwargs),
        "youngest": _top_rows(subset, "age_entreprise", 10, True, **common_kwargs),
    }

    global_ca = (
        float(clustered_frame["chiffre_affaires"].mean())
        if not clustered_frame["chiffre_affaires"].dropna().empty
        else None
    )
    global_eff = (
        float(clustered_frame["nb_employes_mid"].mean())
        if not clustered_frame["nb_employes_mid"].dropna().empty
        else None
    )
    global_age = (
        float(clustered_frame["age_entreprise"].mean())
        if not clustered_frame["age_entreprise"].dropna().empty
        else None
    )
    global_loc = (
        float(clustered_frame["nb_locaux"].mean())
        if not clustered_frame["nb_locaux"].dropna().empty
        else None
    )

    global_comparison = {
        "ca_mean_delta_pct": _pct_delta(ca_stats["mean"], global_ca),
        "effectif_mean_delta_pct": _pct_delta(eff_stats["mean"], global_eff),
        "age_mean_delta_pct": _pct_delta(age_stats["mean"], global_age),
        "nb_locaux_mean_delta_pct": _pct_delta(loc_stats["mean"], global_loc),
    }

    ca_cv = _safe_cv(subset["chiffre_affaires"])
    eff_cv = _safe_cv(subset["nb_employes_mid"])
    age_cv = _safe_cv(subset["age_entreprise"])
    loc_cv = _safe_cv(subset["nb_locaux"])
    is_highly_disperse = any(
        value is not None and value > 1.5 for value in [ca_cv, eff_cv, age_cv]
    )

    return {
        "summary_stats": {
            "count": int(len(subset)),
            "ca": ca_stats,
            "effectif": eff_stats,
            "age": age_stats,
            "nb_locaux": loc_stats,
        },
        "dominant_dimensions": dominant,
        "extremes": extremes,
        "representative_companies": _representative_companies(
            subset,
            5,
            label_map,
            mat_score_map,
            mat_level_map,
        ),
        "top_lists": top_lists,
        "global_comparison": global_comparison,
        "homogeneity": {
            "ca_cv": ca_cv,
            "effectif_cv": eff_cv,
            "age_cv": age_cv,
            "nb_locaux_cv": loc_cv,
            "is_highly_disperse": is_highly_disperse,
            "warning": (
                "Ce segment est tres heterogenee, les moyennes peuvent etre trompeuses."
                if is_highly_disperse
                else ""
            ),
        },
    }



# Encode a text/categorical pandas column into integers for scikit-learn.
# DecisionTreeClassifier cannot train on strings directly, so categories like
# "PME", "IT", or "Small" must become numbers.
def _encode_column(series: pd.Series, fallback: str) -> tuple[pd.Series, dict[str, int]]:
    values = {str(value) for value in series.fillna(fallback).astype(str).tolist()}
    values.add(fallback)
    mapping = {value: index for index, value in enumerate(sorted(values))}
    encoded = series.fillna(fallback).astype(str).map(mapping).fillna(mapping[fallback]).astype(int)
    return encoded, mapping



# Load raw SQLAlchemy rows into a clean pandas DataFrame.
#
# This is the MAIN preprocessing function of the decision-tree segmentation pipeline.
#
# It transforms raw database objects into a table that can be used by:
# 1. the business rule function `segment_label()`
# 2. the Decision Tree model
# 3. the summary JSON
# 4. the frontend dashboard
#
# Main responsibilities:
# - Convert SQLAlchemy objects into pandas rows
# - Clean numeric/date/text fields
# - Remove duplicated companies
# - Normalize company categories
# - Create business features:
#   - region
#   - employee midpoint
#   - company age
#   - macro sector
#   - CA band
# - Create the rule-based training label: `segment_rule`
# - Build fallback revenue values for model prediction
# - Encode text columns into numbers for scikit-learn
def _load_companies_frame(rows: list[Any]) -> tuple[pd.DataFrame, int]:
    # Keep the original number of rows loaded from the database.
    # This is useful for reporting:
    # - total_rows = rows fetched from DB
    # - total_leads = rows kept after cleaning/deduplication
    total_rows = len(rows)

    # Convert SQLAlchemy ORM objects into a pandas DataFrame.
    #
    # Each `row` is an Entreprise object from the database.
    # We extract only the fields needed for segmentation and dashboard display.
    #
    # Important:
    # - Database column names are sometimes different from dashboard/model names.
    # - Example:
    #   - row.nom → nom_entreprise
    #   - row.taille_entrep → tranche_effectif
    #   - row.ca → ca
    frame = pd.DataFrame(
        [
            {
                "siren": row.siren,
                "nom_entreprise": row.nom,
                "ville": row.ville,
                "code_postal": row.code_postal,
                "secteur_activite": row.secteur_activite,
                "categorie_entreprise": row.categorie_entreprise,
                "tranche_effectif": row.taille_entrep,
                "nb_locaux": row.nb_locaux,
                "ca": row.ca,
                "date_creation": row.date_creation_entreprise,
            }
            for row in rows
        ]
    )

    # If the database query returned no usable rows, stop early.
    # The caller will decide whether to raise an error.
    if frame.empty:
        return frame, total_rows

    # -------------------------------------------------------------------------
    # 1. BASIC TYPE CLEANING
    # -------------------------------------------------------------------------

    # Convert revenue/CA to numeric.
    #
    # Why `errors="coerce"`?
    # If a value is invalid, for example:
    # - ""
    # - "N/A"
    # - "unknown"
    # pandas converts it to NaN instead of crashing.
    frame["ca"] = pd.to_numeric(frame["ca"], errors="coerce")

    # Convert number of business locations/sites to numeric.
    # Invalid values also become NaN.
    frame["nb_locaux"] = pd.to_numeric(frame["nb_locaux"], errors="coerce")

    # Convert creation date into pandas datetime.
    # This is required later to calculate company age.
    # Invalid dates become NaT, which is pandas' missing date value.
    frame["date_creation"] = pd.to_datetime(frame["date_creation"], errors="coerce")

    # -------------------------------------------------------------------------
    # 2. DEDUPLICATION
    # -------------------------------------------------------------------------

    # Remove duplicate companies based on SIREN.
    #
    # SIREN is the unique French company identifier.
    # If the same SIREN appears multiple times, we keep only the first occurrence.
    #
    # The condition also keeps rows where SIREN is missing:
    # - frame["siren"].isna() keeps rows without SIREN
    # - ~frame["siren"].duplicated() keeps the first unique SIREN
    frame = frame.loc[frame["siren"].isna() | ~frame["siren"].duplicated()].copy()

    # -------------------------------------------------------------------------
    # 3. TEXT NORMALIZATION / MISSING VALUE CLEANING
    # -------------------------------------------------------------------------

    # Normalize company category names.
    #
    # Example:
    # - "PME" → "Petite et Moyenne Entreprise"
    # - "ETI" → "Entreprise de Taille Intermédiaire"
    # - "Grande entreprise" → "Grande Entreprise"
    #
    # This is important because the Decision Tree uses encoded categories.
    # Without normalization, the same category could appear under many spellings.
    frame["categorie_entreprise"] = frame["categorie_entreprise"].apply(
        normalize_company_category
    )

    # Clean employee range text.
    #
    # Example:
    # - None → ""
    # - " 10 à 19 salariés " → "10 à 19 salariés"
    #
    # This allows correct mapping through EFFECTIF_MAP.
    frame["tranche_effectif"] = (
        frame["tranche_effectif"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Fill missing sector with "Inconnu".
    #
    # Later, unknown sectors become macro sector "Other".
    frame["secteur_activite"] = frame["secteur_activite"].fillna("Inconnu")

    # Fill missing city for frontend display.
    frame["ville"] = frame["ville"].fillna("Inconnu")

    # Fill missing postal code with empty string.
    #
    # _get_region() can safely handle empty strings and return "Inconnu".
    frame["code_postal"] = frame["code_postal"].fillna("")

    # -------------------------------------------------------------------------
    # 4. FEATURE ENGINEERING — BUSINESS/DASHBOARD FEATURES
    # -------------------------------------------------------------------------

    # Create a display-friendly revenue column.
    #
    # `ca` is the raw modeling/source column.
    # `chiffre_affaires` is the name expected by the JSON/frontend.
    frame["chiffre_affaires"] = frame["ca"]

    # Convert postal code into broad region.
    #
    # Example:
    # - 75000 → Ile-de-France
    # - 13000 → Sud
    # - invalid/missing → Inconnu
    #
    # This reduces geographic complexity.
    frame["region"] = frame["code_postal"].apply(_get_region)

    # Convert employee range text into approximate numeric employee count.
    #
    # Example:
    # - "10 à 19 salariés" → 14
    # - "100 à 199 salariés" → 149
    #
    # This gives the dashboard and explainability layer a numeric employee signal.
    frame["nb_employes_mid"] = frame["tranche_effectif"].map(EFFECTIF_MAP)

    # If some employee ranges were unknown or not found in EFFECTIF_MAP,
    # replace missing employee count with the median employee count.
    # Why median instead of mean?
    # Median is more robust when there are very large companies.
    employe_median = frame["nb_employes_mid"].dropna().median()
    frame["nb_employes_mid"] = frame["nb_employes_mid"].fillna(
        employe_median if pd.notna(employe_median) else 0
    )

    # Calculate company age in years.
    #
    # Formula:
    # today - creation date = number of days
    # days / 365.25 = approximate years
    #
    # 365.25 is used to account for leap years approximately.
    frame["age_entreprise"] = (
        pd.Timestamp("today").normalize() - frame["date_creation"]
    ).dt.days / 365.25

    # If age is missing because the creation date was missing/invalid,
    # replace it with the median age.
    age_median = frame["age_entreprise"].dropna().median()
    frame["age_entreprise"] = frame["age_entreprise"].fillna(
        age_median if pd.notna(age_median) else 0
    )

    # -------------------------------------------------------------------------
    # 5. FEATURE ENGINEERING — DECISION TREE SPECIFIC FEATURES
    # -------------------------------------------------------------------------

    # Convert detailed sector labels into broader macro sectors.
    #
    # Example:
    # - "Conseil informatique" → "IT"
    # - "Commerce de gros" → "Commerce"
    # - unknown sector → "Other"
    #
    # This simplifies the sector dimension for the Decision Tree.
    frame["macro_sector"] = frame["secteur_activite"].apply(macro_sector)

    # Convert raw revenue into business bands.
    #
    # Example:
    # - missing CA → "Unknown"
    # - CA < 10M → "Small"
    # - CA < 50M → "Mid"
    # - CA >= 50M → "Large"
    #
    # This makes revenue easier to use in business rules.
    frame["ca_band"] = frame["ca"].apply(ca_band)

    # Apply business rules to create the supervised target label.
    #
    # Example:
    # - PME + Small + IT → PME_Small_IT
    # - ETI + Large CA → ETI_Large
    # - Grande Entreprise → GE_Large
    #
    # This is the target the Decision Tree will learn to predict.
    frame["segment_rule"] = frame.apply(segment_label, axis=1)

    # -------------------------------------------------------------------------
    # 6. MODELING FALLBACK FOR MISSING CA
    # -------------------------------------------------------------------------

    # The tree needs a numeric CA value for every prediction.
    #
    # Problem:
    # Some companies may have missing CA.
    #
    # Solution:
    # Create `ca_for_model`, which fills missing CA in this order:
    # 1. median CA of the same company category
    # 2. global median CA of the full dataset
    # 3. 0.0 as a final fallback
    #
    # Important:
    # - We keep `chiffre_affaires` as the original CA for reporting.
    # - `ca_for_model` is only a modeling helper.
    category_ca_median = frame.groupby("categorie_entreprise")["ca"].transform("median")

    global_ca_median = frame["ca"].dropna().median()
    if pd.isna(global_ca_median):
        global_ca_median = 0.0

    frame["ca_for_model"] = (
        frame["ca"]
        .fillna(category_ca_median)
        .fillna(global_ca_median)
        .fillna(0.0)
    )

    # -------------------------------------------------------------------------
    # 7. ENCODING TEXT COLUMNS FOR SCIKIT-LEARN
    # -------------------------------------------------------------------------

    # scikit-learn DecisionTreeClassifier cannot directly use text values.
    # It needs numeric columns.
    #
    # So we convert text categories into integer codes.
    #
    # Example:
    # - "Petite et Moyenne Entreprise" → 0
    # - "Entreprise de Taille Intermédiaire" → 1
    # - "Grande Entreprise" → 2
    #
    # The exact number is not important; it is just a machine-readable code.
    frame["cat_enc"], _ = _encode_column(
        frame["categorie_entreprise"], "Petite et Moyenne Entreprise"
    )

    # Encode macro sector.
    #
    # Example:
    # - "IT" → integer code
    # - "Commerce" → integer code
    # - missing/unknown → fallback "Other"
    frame["sec_enc"], _ = _encode_column(frame["macro_sector"], "Other")

    # Encode CA band.
    #
    # Example:
    # - "Small" → integer code
    # - "Mid" → integer code
    # - "Large" → integer code
    # - missing → fallback "Unknown"
    frame["band_enc"], _ = _encode_column(frame["ca_band"], "Unknown")

    # Return:
    # - cleaned/enriched dataframe
    # - original DB row count
    return frame, total_rows



# Aggregate all predicted companies into segment summary cards.
# These summary dictionaries become the `segments` array inside
# cluster_summary.json and are consumed directly by the Vue dashboard.
def _build_segment_summaries(frame: pd.DataFrame) -> list[dict[str, Any]]:
    grouped = (
        frame.groupby(["cluster", "segment_code"], dropna=False)
        .agg(
            n=("cluster", "count"),
            employes_moyen=("nb_employes_mid", "mean"),
            ca_moyen=("chiffre_affaires", "mean"),
            nb_locaux_moyen=("nb_locaux", "mean"),
            age_moyen=("age_entreprise", "mean"),
            categorie_dominante=("categorie_entreprise", lambda series: _safe_mode(series, "PME")),
            secteur_dominant=("secteur_activite", lambda series: _safe_mode(series, "Inconnu")),
            region_dominante=("region", lambda series: _safe_mode(series, "Inconnu")),
            macro_sector_dominant=("macro_sector", lambda series: _safe_mode(series, "Other")),
            confidence_moyenne=("decision_tree_confidence", "mean"),
        )
        .reset_index()
        .sort_values("cluster")
    )

    segments: list[dict[str, Any]] = []
    for _, row in grouped.iterrows():
        segment_code = str(row["segment_code"])
        meta = SEGMENT_META.get(segment_code)
        if not meta:
            continue

        segments.append(
            {
                "cluster": int(meta["cluster"]),
                "segment_code": segment_code,
                "label": meta["label"],
                "label_short": meta["label_short"],
                "label_sub": meta["label_sub"],
                "color": meta["color"],
                "recommendation": meta["recommendation"],
                "n": int(row["n"]),
                "employes_moyen": int(round(float(row["employes_moyen"])))
                if not pd.isna(row["employes_moyen"])
                else 0,
                "ca_moyen": round(float(row["ca_moyen"]), 1)
                if not pd.isna(row["ca_moyen"])
                else None,
                "nb_locaux_moyen": round(float(row["nb_locaux_moyen"]), 1)
                if not pd.isna(row["nb_locaux_moyen"])
                else None,
                "age_moyen": round(float(row["age_moyen"]), 1)
                if not pd.isna(row["age_moyen"])
                else None,
                "categorie_dominante": row["categorie_dominante"],
                "secteur_dominant": row["secteur_dominant"],
                "region_dominante": row["region_dominante"],
                "macro_sector_dominant": row["macro_sector_dominant"],
                "decision_tree_confidence_mean": round(float(row["confidence_moyenne"]), 4)
                if not pd.isna(row["confidence_moyenne"])
                else None,
            }
        )

    return segments



# Read the source of generated insights from cluster_insights.json if present.
# This lets the frontend show whether insights came from Gemini or fallback rules.
def _load_insights_source(export_dir: str) -> str:
    path = Path(export_dir) / "cluster_insights.json"
    if not path.exists():
        return ""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return str(payload.get("source") or "")
    except Exception:
        return ""



# Save both latest JSON files and timestamped historical JSON files.
# Latest files are used by the app; timestamped files allow audit/comparison
# between different segmentation runs.
def _save_versioned(
    summary: dict[str, Any],
    leads_records: list[dict[str, Any]],
    export_dir: str,
    timestamp: str,
) -> None:
    path = Path(export_dir)
    path.mkdir(parents=True, exist_ok=True)

    for filename in (f"cluster_summary_{timestamp}.json", "cluster_summary.json"):
        with open(path / filename, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, default=str)

    for filename in (f"clustered_leads_{timestamp}.json", "clustered_leads.json"):
        with open(path / filename, "w", encoding="utf-8") as handle:
            json.dump(leads_records, handle, ensure_ascii=False, default=str)



# Main production entry point for the decision-tree segmentation engine.
# FastAPI calls this function indirectly through run_clustering() compatibility.
# It orchestrates the entire flow from DB rows to saved JSON outputs.
def run_decision_tree_segmentation(
    db: Session,
    export_dir: str = DEFAULT_EXPORT_DIR,
) -> dict[str, Any]:
    from db.models import Entreprise

    # Timestamp used for versioned JSON filenames, e.g. cluster_summary_20260428_1651.json.
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")

    # Load all company rows from the ETL database.
    rows = db.query(Entreprise).all()
    if not rows:
        raise ValueError("No data in entreprise table. Run the ETL pipeline first.")

    # Convert raw ORM rows into a cleaned and feature-engineered pandas DataFrame.
    frame, total_rows = _load_companies_frame(rows)
    if frame.empty:
        raise ValueError("No rows could be prepared for segmentation.")

    # Training rows must have a rule-based target and a real CA value.
    # Rows with missing CA can still be predicted later using ca_for_model.
    train_frame = frame[frame["segment_rule"].notna() & frame["ca"].notna()].copy()
    if train_frame.empty:
        raise ValueError("Not enough labelled rows to train decision-tree segmentation.")

    # Shallow tree: intentionally simple so rules stay explainable.
    # min_samples_leaf avoids tiny unreliable leaves.
    # random_state keeps runs reproducible.
    model = DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=20,
        random_state=42,
    )

    # X_train = numeric inputs. y_train = business segment labels.
    X_train = train_frame[TREE_FEATURE_COLUMNS].astype(float)
    y_train = train_frame["segment_rule"].astype(str)

    # Fit means: teach the Decision Tree how inputs map to segment labels.
    model.fit(X_train, y_train)
    y_train_pred = model.predict(X_train)

    # Build prediction features for every company, including rows with missing CA.
    # For prediction, we use ca_for_model because it has safe fallback values.
    X_all = pd.DataFrame(
        {
            "cat_enc": frame["cat_enc"],
            "ca": frame["ca_for_model"],
            "sec_enc": frame["sec_enc"],
            "band_enc": frame["band_enc"],
        }
    ).astype(float)

    # Predict the final segment and confidence for every company.
    predicted_segments = model.predict(X_all)
    predicted_proba = model.predict_proba(X_all)
    frame["segment_code"] = predicted_segments
    frame["cluster"] = frame["segment_code"].map(
        lambda code: SEGMENT_META.get(str(code), {}).get("cluster", -1)
    )
    frame["decision_tree_confidence"] = np.round(predicted_proba.max(axis=1), 4)

    # Build supervised-model validation metrics: accuracy, rules, depth, leaves, etc.
    validation = compute_decision_tree_validation(
        model=model,
        X_train=X_train,
        y_true=y_train,
        y_pred=y_train_pred,
        feature_names=TREE_FEATURE_DISPLAY_NAMES,
        segment_count=int(frame["cluster"].nunique()),
    )

    # Aggregate company-level predictions into segment-level summaries.
    segments = _build_segment_summaries(frame)

    # Compute segment-vs-global explainability values.
    explain_map = compute_explainability(frame)
    for segment in segments:
        compute_maturity(segment)
        segment["explainability"] = explain_map.get(segment["cluster"], {})

    # Generate optional LLM explanations for maturity. Fallback logic lives in that module.
    maturity_llm_map = generate_all_maturity_analyses(segments, export_dir, timestamp)
    for segment in segments:
        cluster_id = int(segment["cluster"])
        segment["llm_analysis"] = maturity_llm_map.get(cluster_id, {})

    label_map = {segment["cluster"]: segment["label"] for segment in segments}
    color_map = {segment["cluster"]: segment["color"] for segment in segments}
    mat_score_map = {
        segment["cluster"]: segment["digital_maturity_score"] for segment in segments
    }
    mat_level_map = {
        segment["cluster"]: segment["digital_maturity_level"] for segment in segments
    }

    # Keep only the columns needed by the segment drilldown/details UI.
    drilldown_frame = frame[
        [
            "siren",
            "nom_entreprise",
            "ville",
            "secteur_activite",
            "categorie_entreprise",
            "tranche_effectif",
            "chiffre_affaires",
            "age_entreprise",
            "region",
            "cluster",
            "nb_employes_mid",
            "nb_locaux",
            "macro_sector",
            "ca_band",
            "decision_tree_confidence",
            "segment_rule",
            "ca_for_model",
        ]
    ].copy()

    for segment in segments:
        segment["drilldown"] = _build_drilldown(
            cluster_id=int(segment["cluster"]),
            clustered_frame=drilldown_frame,
            label_map=label_map,
            mat_score_map=mat_score_map,
            mat_level_map=mat_level_map,
        )

    # Generate strategic insights for the dashboard.
    insights = generate_insights(segments, validation, export_dir, timestamp)
    insights_source = _load_insights_source(export_dir)
    maturity_overview = build_maturity_overview(segments)

    run_at = datetime.utcnow().isoformat() + "Z"
    # Final summary JSON returned by FastAPI and saved as cluster_summary.json.
    result_summary = {
        "status": "ok",
        "run_at": run_at,
        "model_type": MODEL_TYPE,
        "k_used": len(segments),
        "total_rows": int(total_rows),
        "total_leads": int(len(frame)),
        "validation": validation,
        "segments": segments,
        "insights": insights,
        "insights_source": insights_source,
        "maturity_overview": maturity_overview,
        "tree_rules": validation.get("tree_rules"),
        "training_accuracy": validation.get("training_accuracy"),
    }

    # Lead-level JSON exported as clustered_leads.json.
    clustered_frame = frame[
        [
            "siren",
            "nom_entreprise",
            "ville",
            "secteur_activite",
            "categorie_entreprise",
            "tranche_effectif",
            "chiffre_affaires",
            "age_entreprise",
            "region",
            "cluster",
            "macro_sector",
            "ca_band",
            "decision_tree_confidence",
            "segment_rule",
        ]
    ].copy()
    clustered_frame["cluster_label"] = clustered_frame["cluster"].map(
        lambda cluster_id: label_map.get(int(cluster_id), f"Cluster {cluster_id}")
    )
    clustered_frame["cluster_color"] = clustered_frame["cluster"].map(
        lambda cluster_id: color_map.get(int(cluster_id), "#888")
    )
    clustered_frame["age_entreprise"] = clustered_frame["age_entreprise"].round(1)

    leads_records = json.loads(
        clustered_frame.to_json(orient="records", force_ascii=False, default_handler=str)
    )
    segment_scores = clustered_frame["cluster"].map(
        lambda cluster_id: mat_score_map.get(int(cluster_id), 5.0)
    ).tolist()
    segment_levels = clustered_frame["cluster"].map(
        lambda cluster_id: mat_level_map.get(int(cluster_id), "Moyen")
    ).tolist()

    # Add per-lead maturity fields based on the maturity of the assigned segment.
    for index, lead in enumerate(leads_records):
        compute_lead_maturity(lead, segment_scores[index], segment_levels[index])

    # Persist latest + versioned JSON outputs, then return summary to the API caller.
    _save_versioned(result_summary, leads_records, export_dir, timestamp)
    return result_summary
