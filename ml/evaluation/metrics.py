"""Calcul des metriques de classification pour le modele predictif (Etape 17)."""

from typing import Any

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
) -> dict[str, Any]:
    """
    Calculer les metriques standard d'evaluation d'un classifieur binaire.

    y_proba doit contenir la probabilite de la classe positive
    (readmitted_30_days = 1).
    """
    true_negative, false_positive, false_negative, true_positive = (
        confusion_matrix(y_true, y_pred).ravel()
    )

    sensitivity = recall_score(y_true, y_pred, zero_division=0)

    specificity = (
        true_negative / (true_negative + false_positive)
        if (true_negative + false_positive) > 0
        else 0.0
    )

    return {
        "precision": round(
            float(precision_score(y_true, y_pred, zero_division=0)), 4
        ),
        "recall": round(float(sensitivity), 4),
        "sensitivity": round(float(sensitivity), 4),
        "specificity": round(float(specificity), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_proba)), 4),
        "pr_auc": round(float(average_precision_score(y_true, y_proba)), 4),
        "confusion_matrix": {
            "true_negative": int(true_negative),
            "false_positive": int(false_positive),
            "false_negative": int(false_negative),
            "true_positive": int(true_positive),
        },
    }
