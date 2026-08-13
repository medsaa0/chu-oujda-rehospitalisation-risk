from ml.prediction.predict import categorize_risk


def test_below_medium_threshold_is_low() -> None:
    assert categorize_risk(0.1, medium_threshold=0.5, high_threshold=0.7) == "Low"


def test_between_thresholds_is_medium() -> None:
    assert categorize_risk(0.6, medium_threshold=0.5, high_threshold=0.7) == "Medium"


def test_above_high_threshold_is_high() -> None:
    assert categorize_risk(0.9, medium_threshold=0.5, high_threshold=0.7) == "High"


def test_boundaries_are_inclusive_lower_bound() -> None:
    assert categorize_risk(0.5, medium_threshold=0.5, high_threshold=0.7) == "Medium"
    assert categorize_risk(0.7, medium_threshold=0.5, high_threshold=0.7) == "High"
