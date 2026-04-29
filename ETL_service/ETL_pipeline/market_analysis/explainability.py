"""
market_analysis/explainability.py
==================================
Cluster explainability: identifies the features that differentiate each cluster
most strongly from the global average.

Output per cluster:
    "explainability": {
        "top_features": [
            {"feature": "ca_log", "direction": "above", "ratio": 2.3,
             "description": "CA 2.3× supérieur à la moyenne globale"}
        ],
        "comparisons": {
            "nb_employes_mid": {"cluster_mean": 4468, "global_mean": 312, "ratio": 14.3}
        }
    }
"""

import numpy as np
import pandas as pd


# Human-readable feature descriptions for the CEO (no technical ML jargon)
FEATURE_LABELS = {
    "nb_employes_mid": "Effectif moyen",
    "ca_log":          "Chiffre d'affaires (log)",
    "chiffre_affaires":"CA réel (€)",
    "nb_locaux_log":   "Nombre de sites (log)",
    "nb_locaux":       "Nombre de sites",
    "age_entreprise":  "Ancienneté (années)",
}

# Features to include in explainability (numeric, pre-scaling)
EXPLAIN_FEATURES = [
    "nb_employes_mid",
    "chiffre_affaires",
    "nb_locaux",
    "age_entreprise",
]


def compute_explainability(df: pd.DataFrame) -> dict[int, dict]:
    """
    For each cluster in df['cluster'], compute feature comparisons vs global.

    Returns: { cluster_id: {"top_features": [...], "comparisons": {...}} }
    """
    global_means = {}
    global_stds  = {}
    for feat in EXPLAIN_FEATURES:
        if feat in df.columns:
            vals = df[feat].dropna()
            global_means[feat] = float(vals.mean()) if len(vals) else 0.0
            global_stds[feat]  = float(vals.std())  if len(vals) else 1.0

    result = {}
    for cluster_id in sorted(df["cluster"].unique()):
        subset = df[df["cluster"] == cluster_id]
        comparisons = {}
        scored = []

        for feat in EXPLAIN_FEATURES:
            if feat not in df.columns:
                continue
            vals = subset[feat].dropna()
            if len(vals) == 0:
                continue

            c_mean   = float(vals.mean())
            g_mean   = global_means[feat]
            g_std    = global_stds[feat]

            # Ratio relative to global (handle near-zero)
            ratio = c_mean / (g_mean + 1e-9)
            # Z-score: how many stds above/below global
            z     = (c_mean - g_mean) / (g_std + 1e-9)

            direction = "above" if c_mean > g_mean else "below"
            direction_fr = "supérieur" if direction == "above" else "inférieur"
            label    = FEATURE_LABELS.get(feat, feat)
            desc     = f"{label} {abs(ratio):.1f}× {direction_fr} à la moyenne globale"

            comparisons[feat] = {
                "cluster_mean": round(c_mean, 2),
                "global_mean":  round(g_mean,  2),
                "ratio":        round(ratio,   2),
                "z_score":      round(z,       2),
                "direction":    direction,
            }
            scored.append((feat, abs(z), direction, desc, round(ratio, 2)))

        # Sort by absolute z-score, take top 3
        scored.sort(key=lambda x: x[1], reverse=True)
        top_features = [
            {
                "feature":     f,
                "direction":   d,
                "ratio":       r,
                "description": desc_text,
            }
            for f, _, d, desc_text, r in scored[:3]
        ]

        result[int(cluster_id)] = {
            "top_features": top_features,
            "comparisons":  comparisons,
        }

    return result
