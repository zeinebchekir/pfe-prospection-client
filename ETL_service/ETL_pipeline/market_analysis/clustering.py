"""
market_analysis/clustering.py  (v2 — production upgrade)
=========================================================
Full KMeans pipeline with:
  - Data-driven labeling          (labeling.py)
  - Model validation              (validation.py)
  - Cluster explainability        (explainability.py)
  - Gemini LLM insights           (llm_service.py)
  - Versioned JSON output
  - Backward-compatible JSON schema
"""

from __future__ import annotations

import os
import json
import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session

from market_analysis.labeling        import assign_labels
from market_analysis.validation      import compute_validation
from market_analysis.explainability  import compute_explainability
from market_analysis.llm_service     import generate_insights, load_insights

warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
K_FINAL       = 5
DEFAULT_EXPORT_DIR = os.environ.get(
    "SEGMENTATION_EXPORT_DIR", "/opt/airflow/exports/segmentation"
)

# Employee midpoint table
EFFECTIF_MAP = {
    "Unité non employeuse (0 salarié)": 0, "0 salarié": 0,
    "1 à 2 salariés": 1,   "3 à 5 salariés": 4,   "6 à 9 salariés": 7,
    "10 à 19 salariés": 14,"20 à 49 salariés": 34, "50 à 99 salariés": 74,
    "100 à 199 salariés": 149, "200 à 249 salariés": 224,
    "250 à 499 salariés": 374, "500 à 999 salariés": 749,
    "1 000 à 1 999 salariés": 1499, "2 000 à 4 999 salariés": 3499,
    "5 000 à 9 999 salariés": 7499, "10 000 salariés et plus": 15000,
}


def _get_region(cp) -> str:
    try:
        dept = int(str(cp)) // 1000
        if 75 <= dept <= 95: return "Ile-de-France"
        elif dept <= 30:     return "Sud"
        elif dept <= 55:     return "Est"
        elif dept <= 76:     return "Nord-Ouest"
        else:                return "Autre"
    except Exception:
        return "Inconnu"


# ── Main entry point ──────────────────────────────────────────────────────────

def run_clustering(db: Session, export_dir: str = DEFAULT_EXPORT_DIR) -> dict:
    """
    Full pipeline: fetch → clean → engineer → cluster → validate →
    explain → label → LLM insights → version & save → return summary.

    Returns the same structure as v1 for backward compatibility,
    extended with: validation, insights, and per-segment explainability.
    """
    from db.models import Entreprise

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")

    # ── 1. Load ───────────────────────────────────────────────────────────────
    rows = db.query(Entreprise).all()
    if not rows:
        raise ValueError("No data in entreprise table. Run the ETL pipeline first.")

    df = pd.DataFrame([{
        "siren":                r.siren,
        "nom_entreprise":       r.nom,
        "ville":                r.ville,
        "code_postal":          r.code_postal,
        "secteur_activite":     r.secteur_activite,
        "categorie_entreprise": r.categorie_entreprise or "PME",
        "tranche_effectif":     r.taille_entrep,
        "nb_locaux":            r.nb_locaux,
        "chiffre_affaires":     r.ca,
        "date_creation":        r.date_creation_entreprise,
    } for r in rows])
    print(f"[clustering] Loaded {len(df)} rows from DB")

    # ── 2. Clean ──────────────────────────────────────────────────────────────
    for col in ["nb_locaux", "chiffre_affaires"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates(subset=["siren"])
    df["categorie_entreprise"] = df["categorie_entreprise"].fillna("PME")

    # ── 3. Feature Engineering ────────────────────────────────────────────────
    df["nb_employes_mid"] = df["tranche_effectif"].str.strip().map(EFFECTIF_MAP)
    df["nb_employes_mid"] = df["nb_employes_mid"].fillna(df["nb_employes_mid"].median())

    df["ca_log"] = np.log1p(df["chiffre_affaires"])
    med_ca = df.groupby("categorie_entreprise")["ca_log"].transform("median")
    df["ca_log"] = df["ca_log"].fillna(med_ca).fillna(df["ca_log"].median())

    df["nb_locaux_log"] = np.log1p(df["nb_locaux"].fillna(1))

    df["date_creation"] = pd.to_datetime(df["date_creation"], errors="coerce")
    df["age_entreprise"] = (
        pd.Timestamp("today") - df["date_creation"]
    ).dt.days / 365.25
    df["age_entreprise"] = df["age_entreprise"].fillna(df["age_entreprise"].median())

    df["region"] = df["code_postal"].apply(_get_region)

    top_sectors = df["secteur_activite"].value_counts().head(8).index.tolist()
    df["secteur_broad"] = df["secteur_activite"].apply(
        lambda x: x if x in top_sectors else "Autre"
    )

    # ── 4. Feature Matrix ─────────────────────────────────────────────────────
    NUM_FEATURES = ["nb_employes_mid", "ca_log", "nb_locaux_log", "age_entreprise"]
    CAT_FEATURES = ["categorie_entreprise", "region", "secteur_broad"]

    X_num = df[NUM_FEATURES].copy()
    X_cat = pd.get_dummies(df[CAT_FEATURES], drop_first=False)
    X_raw = pd.concat([X_num, X_cat], axis=1)

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    # ── 5. KMeans ─────────────────────────────────────────────────────────────
    km = KMeans(n_clusters=K_FINAL, random_state=42, n_init=20)
    labels_arr = km.fit_predict(X)
    df["cluster"] = labels_arr
    print(f"[clustering] KMeans K={K_FINAL} fitted. Inertia={km.inertia_:.0f}")

    # ── 6. Model Validation ───────────────────────────────────────────────────
    validation = compute_validation(X, labels_arr, K_FINAL)
    print(f"[clustering] Silhouette={validation['silhouette']} | Best K={validation['elbow']['best_k']}")

    # ── 7. Cluster Summary (raw stats) ────────────────────────────────────────
    summary_df = df.groupby("cluster").agg(
        n=("cluster", "count"),
        employes_moyen=("nb_employes_mid", "mean"),
        ca_moyen=("chiffre_affaires", "mean"),
        nb_locaux_moyen=("nb_locaux", "mean"),
        age_moyen=("age_entreprise", "mean"),
        categorie_dominante=("categorie_entreprise", lambda x: x.mode()[0]),
        secteur_dominant=("secteur_broad", lambda x: x.mode()[0]),
        region_dominante=("region", lambda x: x.mode()[0]),
    ).reset_index()

    for col in ["employes_moyen", "ca_moyen", "nb_locaux_moyen", "age_moyen"]:
        summary_df[col] = summary_df[col].round(
            0 if col == "employes_moyen" else 1
        )

    # ── 8. Explainability ────────────────────────────────────────────────────
    explain_map = compute_explainability(df)

    # ── 9. Dynamic Labeling ───────────────────────────────────────────────────
    raw_segments = []
    for _, row in summary_df.iterrows():
        c = int(row["cluster"])
        raw_segments.append({
            "cluster":             c,
            "n":                   int(row["n"]),
            "employes_moyen":      int(row["employes_moyen"]),
            "ca_moyen":            float(row["ca_moyen"]) if not pd.isna(row["ca_moyen"]) else None,
            "nb_locaux_moyen":     float(row["nb_locaux_moyen"]) if not pd.isna(row["nb_locaux_moyen"]) else None,
            "age_moyen":           float(row["age_moyen"]),
            "categorie_dominante": row["categorie_dominante"],
            "secteur_dominant":    row["secteur_dominant"],
            "region_dominante":    row["region_dominante"],
        })

    # assign_labels injects label / color / recommendation
    segments = assign_labels(raw_segments, df)

    # Attach explainability per segment
    for seg in segments:
        seg["explainability"] = explain_map.get(seg["cluster"], {})

    # ── 10. LLM Insights (Gemini) ─────────────────────────────────────────────
    insights = generate_insights(segments, validation, export_dir, timestamp)

    # ── 11. Build Final Summary ───────────────────────────────────────────────
    run_at = datetime.utcnow().isoformat() + "Z"
    result_summary = {
        "run_at":      run_at,
        "k_used":      K_FINAL,
        "total_leads": len(df),
        "validation":  validation,
        "segments":    segments,
        "insights":    insights,
    }

    # ── 12. Export Clustered Leads ────────────────────────────────────────────
    # Build label map from dynamic assignment
    label_map = {s["cluster"]: s["label"] for s in segments}
    color_map = {s["cluster"]: s["color"] for s in segments}

    clustered_df = df[[
        "siren", "nom_entreprise", "ville", "secteur_activite",
        "categorie_entreprise", "tranche_effectif", "chiffre_affaires",
        "age_entreprise", "region", "cluster",
    ]].copy()
    clustered_df["cluster_label"] = clustered_df["cluster"].map(
        lambda c: label_map.get(int(c), f"Cluster {c}")
    )
    clustered_df["cluster_color"] = clustered_df["cluster"].map(
        lambda c: color_map.get(int(c), "#888")
    )
    clustered_df["age_entreprise"] = clustered_df["age_entreprise"].round(1)

    # ── 13. Versioned Save ────────────────────────────────────────────────────
    _save_versioned(result_summary, clustered_df, export_dir, timestamp)

    print(f"[clustering] Done ✓ — timestamp={timestamp}")
    return result_summary


# ── File I/O helpers ──────────────────────────────────────────────────────────

def _save_versioned(
    summary: dict,
    leads_df: pd.DataFrame,
    export_dir: str,
    timestamp: str,
) -> None:
    """
    Save:
      cluster_summary_YYYYMMDD_HHMM.json   (versioned)
      clustered_leads_YYYYMMDD_HHMM.json   (versioned)
      cluster_summary.json                  (latest, overwritten)
      clustered_leads.json                  (latest, overwritten)
    """
    path = Path(export_dir)
    path.mkdir(parents=True, exist_ok=True)

    leads_records = json.loads(
        leads_df.to_json(orient="records", force_ascii=False, default_handler=str)
    )

    # Summary
    for fname in (f"cluster_summary_{timestamp}.json", "cluster_summary.json"):
        with open(path / fname, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, default=str)

    # Leads
    for fname in (f"clustered_leads_{timestamp}.json", "clustered_leads.json"):
        with open(path / fname, "w", encoding="utf-8") as f:
            json.dump(leads_records, f, ensure_ascii=False, default=str)

    print(f"[clustering] Saved versioned files (ts={timestamp})")
