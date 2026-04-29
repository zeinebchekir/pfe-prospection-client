"""
market_analysis/validation.py
==============================
Model validation: silhouette score + elbow curve.

- Silhouette score: measures cluster cohesion vs separation (range: -1 → 1).
  > 0.5 = good, > 0.3 = acceptable, < 0.2 = poor
- Elbow inertia: WCSS for K=2..10 to justify K choice.
- Auto-select K: picks the K with largest marginal inertia drop (elbow point).
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report, confusion_matrix, silhouette_score
from sklearn.tree import export_text


K_MIN = 2
K_MAX = 10


def compute_validation(X: np.ndarray, labels: np.ndarray, k_used: int) -> dict:
    """
    Compute silhouette score for the fitted clustering and elbow inertias.

    Args:
        X:      scaled feature matrix (rows = samples)
        labels: cluster assignment array from fitted KMeans
        k_used: K value actually used

    Returns:
        {
          "k_used":          int,
          "silhouette":      float,       # -1..1
          "silhouette_interpretation": str,
          "elbow": {
              "k_values":   [2,3,...,10],
              "inertias":   [float,...],
              "best_k":     int,          # elbow point
          }
        }
    """
    # ── Silhouette ────────────────────────────────────────────────────────────
    try:
        sil = float(silhouette_score(X, labels))
    except Exception:
        sil = 0.0

    if sil >= 0.5:
        sil_label = "Excellent — clusters très cohérents"
    elif sil >= 0.3:
        sil_label = "Acceptable — structure identifiable"
    elif sil >= 0.1:
        sil_label = "Faible — chevauchement partiel"
    else:
        sil_label = "Mauvais — clusters non distincts"

    # ── Elbow ─────────────────────────────────────────────────────────────────
    k_range  = list(range(K_MIN, K_MAX + 1))
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)
        inertias.append(float(km.inertia_))

    best_k = _elbow_point(k_range, inertias)

    return {
        "k_used":                    k_used,
        "silhouette":                round(sil, 4),
        "silhouette_interpretation": sil_label,
        "elbow": {
            "k_values":  k_range,
            "inertias":  [round(v, 2) for v in inertias],
            "best_k":    best_k,
        },
    }


def _elbow_point(k_values: list[int], inertias: list[float]) -> int:
    """
    Kneedle-inspired elbow detection:
    Normalise both axes to [0,1], compute perpendicular distance of each
    point to the line first→last, return K with max distance.
    """
    n   = len(inertias)
    xs  = np.array(k_values,  dtype=float)
    ys  = np.array(inertias,  dtype=float)

    # Normalise
    xs = (xs - xs[0]) / (xs[-1] - xs[0] + 1e-9)
    ys = (ys - ys[-1]) / (ys[0]  - ys[-1] + 1e-9)

    # Vector from first to last point
    v  = np.array([xs[-1] - xs[0], ys[-1] - ys[0]])
    v /= np.linalg.norm(v) + 1e-9

    dists = []
    for i in range(n):
        p  = np.array([xs[i] - xs[0], ys[i] - ys[0]])
        d  = abs(p[0] * v[1] - p[1] * v[0])
        dists.append(d)

    best_idx = int(np.argmax(dists))
    return k_values[best_idx]


def compute_decision_tree_validation(
    model,
    X_train,
    y_true,
    y_pred,
    feature_names: list[str],
    segment_count: int,
) -> dict:
    """
    Compute validation metrics for the decision-tree segmentation pipeline while
    keeping a frontend-friendly validation object.
    """
    labels = sorted({str(value) for value in y_true.astype(str).tolist()})
    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    training_accuracy = float(model.score(X_train, y_true))

    return {
        "model_type": "decision_tree",
        "k_used": int(segment_count),
        "training_accuracy": round(training_accuracy, 4),
        "tree_depth": int(model.get_depth()),
        "n_leaves": int(model.get_n_leaves()),
        "silhouette": None,
        "silhouette_score": None,
        "silhouette_interpretation": "Not applicable for decision-tree segmentation",
        "elbow": None,
        "classification_report": _round_nested(report),
        "confusion_matrix": {
            "labels": labels,
            "matrix": matrix.tolist(),
        },
        "tree_rules": export_text(model, feature_names=feature_names),
    }


def _round_nested(value):
    if isinstance(value, dict):
        return {key: _round_nested(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_round_nested(item) for item in value]
    if isinstance(value, (float, np.floating)):
        return round(float(value), 4)
    if isinstance(value, (int, np.integer)):
        return int(value)
    return value
