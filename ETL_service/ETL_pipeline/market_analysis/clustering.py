"""
market_analysis/clustering.py
=============================
Refactored from lead_clustering.py.
- Input  : SQLAlchemy Session (reads from `entreprise` table directly)
- Output : cluster_summary.json + clustered_leads.json in EXPORT_DIR
- Returns: summary list for inline API response
"""

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

warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
K_FINAL       = 5
DEFAULT_EXPORT_DIR = os.environ.get(
    "SEGMENTATION_EXPORT_DIR", "/opt/airflow/exports/segmentation"
)

# Business labels: map cluster int → human label (stable with random_state=42)
SEGMENT_LABELS = {
    0: {"name": "PME énergie & retail",               "color": "#F29F05", "recommendation": "Vertical niche"},
    1: {"name": "Grands groupes matures",              "color": "#303E8C", "recommendation": "Enterprise focus"},
    2: {"name": "ETI établies diversifiées",           "color": "#04ADBF", "recommendation": "Relationship selling"},
    3: {"name": "Petites structures jeunes",           "color": "#56A632", "recommendation": "Self-serve"},
    4: {"name": "ETI historiques – commerce de gros",  "color": "#2D3773", "recommendation": "Scalable offers"},
}

# Employee midpoint mapping (same as original script)
EFFECTIF_MAP = {
    "Unité non employeuse (0 salarié)": 0, "0 salarié": 0,
    "1 à 2 salariés": 1, "3 à 5 salariés": 4, "6 à 9 salariés": 7,
    "10 à 19 salariés": 14, "20 à 49 salariés": 34, "50 à 99 salariés": 74,
    "100 à 199 salariés": 149, "200 à 249 salariés": 224,
    "250 à 499 salariés": 374, "500 à 999 salariés": 749,
    "1 000 à 1 999 salariés": 1499, "2 000 à 4 999 salariés": 3499,
    "5 000 à 9 999 salariés": 7499, "10 000 salariés et plus": 15000,
}


def _get_region(cp):
    try:
        dept = int(str(cp)) // 1000
        if 75 <= dept <= 95: return "Ile-de-France"
        elif dept <= 30:     return "Sud"
        elif dept <= 55:     return "Est"
        elif dept <= 76:     return "Nord-Ouest"
        else:                return "Autre"
    except Exception:
        return "Inconnu"


def run_clustering(db: Session, export_dir: str = DEFAULT_EXPORT_DIR) -> dict:
    """
    Fetch all entreprises, run KMeans K=5, persist JSON, return summary.
    Returns: { run_at, total_rows, segments: [ {cluster, label, ...} ] }
    """
    from db.models import Entreprise  # local import to avoid circular

    # ── 1. Load from DB ───────────────────────────────────────────────────────
    rows = db.query(Entreprise).all()
    if not rows:
        raise ValueError("No data in entreprise table. Run the ETL pipeline first.")

    df = pd.DataFrame([{
        "siren":               r.siren,
        "nom_entreprise":      r.nom,
        "ville":               r.ville,
        "code_postal":         r.code_postal,
        "secteur_activite":    r.secteur_activite,
        "categorie_entreprise": r.categorie_entreprise or "PME",
        "tranche_effectif":    r.taille_entrep,
        "nb_locaux":           r.nb_locaux,
        "chiffre_affaires":    r.ca,
        "date_creation":       r.date_creation_entreprise,
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
    df["age_entreprise"] = (pd.Timestamp("2026-04-15") - df["date_creation"]).dt.days / 365.25
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

    # ── 5. KMeans K=5 ─────────────────────────────────────────────────────────
    km = KMeans(n_clusters=K_FINAL, random_state=42, n_init=20)
    df["cluster"] = km.fit_predict(X)

    # ── 6. Cluster Summary ────────────────────────────────────────────────────
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

    summary_df["employes_moyen"]  = summary_df["employes_moyen"].round(0).astype(int)
    summary_df["ca_moyen"]        = summary_df["ca_moyen"].round(0)
    summary_df["nb_locaux_moyen"] = summary_df["nb_locaux_moyen"].round(1)
    summary_df["age_moyen"]       = summary_df["age_moyen"].round(1)

    run_at = datetime.utcnow().isoformat() + "Z"
    total  = len(df)

    # Enrich with business labels
    segments = []
    for _, row in summary_df.iterrows():
        c = int(row["cluster"])
        label_info = SEGMENT_LABELS.get(c, {"name": f"Cluster {c}", "color": "#888", "recommendation": "-"})
        segments.append({
            "cluster":              c,
            "label":                label_info["name"],
            "color":                label_info["color"],
            "recommendation":       label_info["recommendation"],
            "n":                    int(row["n"]),
            "employes_moyen":       int(row["employes_moyen"]),
            "ca_moyen":             float(row["ca_moyen"]) if not pd.isna(row["ca_moyen"]) else None,
            "nb_locaux_moyen":      float(row["nb_locaux_moyen"]) if not pd.isna(row["nb_locaux_moyen"]) else None,
            "age_moyen":            float(row["age_moyen"]),
            "categorie_dominante":  row["categorie_dominante"],
            "secteur_dominant":     row["secteur_dominant"],
            "region_dominante":     row["region_dominante"],
        })

    result_summary = {"run_at": run_at, "total_leads": total, "segments": segments}

    # ── 7. Clustered Leads ────────────────────────────────────────────────────
    clustered_df = df[[
        "siren", "nom_entreprise", "ville", "secteur_activite",
        "categorie_entreprise", "tranche_effectif", "chiffre_affaires",
        "age_entreprise", "region", "cluster",
    ]].copy()
    clustered_df["cluster_label"] = clustered_df["cluster"].map(
        lambda c: SEGMENT_LABELS.get(int(c), {}).get("name", f"Cluster {c}")
    )
    clustered_df["age_entreprise"] = clustered_df["age_entreprise"].round(1)

    # ── 8. Export JSON ────────────────────────────────────────────────────────
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)

    summary_path = export_path / "cluster_summary.json"
    leads_path   = export_path / "clustered_leads.json"

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(result_summary, f, ensure_ascii=False, default=str)

    clustered_df.to_json(leads_path, orient="records", force_ascii=False)

    print(f"[clustering] Done. Summary → {summary_path} | Leads → {leads_path}")
    return result_summary
