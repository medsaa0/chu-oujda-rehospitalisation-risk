import numpy as np

from ml.evaluation.metrics import compute_classification_metrics


def test_perfect_classifier_has_auc_one() -> None:
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 1])
    y_proba = np.array([0.1, 0.2, 0.8, 0.9])

    metrics = compute_classification_metrics(y_true, y_pred, y_proba)

    assert metrics["roc_auc"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["confusion_matrix"]["true_positive"] == 2
    assert metrics["confusion_matrix"]["false_positive"] == 0


def test_confusion_matrix_counts_are_consistent() -> None:
    y_true = np.array([0, 0, 1, 1, 1])
    y_pred = np.array([0, 1, 1, 0, 1])
    y_proba = np.array([0.2, 0.6, 0.7, 0.4, 0.9])

    metrics = compute_classification_metrics(y_true, y_pred, y_proba)
    confusion = metrics["confusion_matrix"]

    total = (
        confusion["true_negative"]
        + confusion["false_positive"]
        + confusion["false_negative"]
        + confusion["true_positive"]
    )

    assert total == len(y_true)
    assert confusion["true_positive"] == 2
    assert confusion["false_negative"] == 1


def test_specificity_and_sensitivity_are_between_zero_and_one() -> None:
    y_true = np.array([0, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 1, 0, 0])
    y_proba = np.array([0.1, 0.9, 0.55, 0.6, 0.3, 0.45])

    metrics = compute_classification_metrics(y_true, y_pred, y_proba)

    assert 0.0 <= metrics["sensitivity"] <= 1.0
    assert 0.0 <= metrics["specificity"] <= 1.0
