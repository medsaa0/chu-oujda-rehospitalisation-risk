"""Dependances partagees de l'API (connexion PostgreSQL, modele ML)."""

import json
from functools import lru_cache
from typing import Any

import joblib
from sqlalchemy.engine import Engine

from src.utils.database import get_engine
from src.utils.paths import MODELS_DIR, ROOT_DIR

PREDICTION_REPORT_PATH = (
    ROOT_DIR / "reports" / "ml" / "prediction_report_latest.json"
)
BEST_MODEL_PATH = MODELS_DIR / "best_model.joblib"


@lru_cache(maxsize=1)
def get_db_engine() -> Engine:
    """Retourner un moteur PostgreSQL partage entre les requetes."""
    return get_engine()


class ModelBundle:
    """Regroupe le pipeline entraine et les seuils de risque associes."""

    def __init__(
        self,
        pipeline: Any,
        model_name: str,
        medium_threshold: float,
        high_threshold: float,
    ) -> None:
        self.pipeline = pipeline
        self.model_name = model_name
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold

    def categorize(self, probability: float) -> str:
        """Traduire une probabilite en categorie de risque."""
        if probability < self.medium_threshold:
            return "Low"

        if probability < self.high_threshold:
            return "Medium"

        return "High"


@lru_cache(maxsize=1)
def get_model_bundle() -> ModelBundle:
    """
    Charger le meilleur modele et ses seuils de risque (mis en cache).

    Leve FileNotFoundError si l'entrainement (Etape 17) n'a pas encore
    ete execute ; l'endpoint /api/predict traduit cette erreur en 503.
    """
    if not BEST_MODEL_PATH.exists():
        raise FileNotFoundError(
            "Aucun modele entraine. Execute d'abord "
            "python -m ml.training.train_models puis "
            "python -m ml.prediction.predict."
        )

    if not PREDICTION_REPORT_PATH.exists():
        raise FileNotFoundError(
            "Aucun rapport de prediction. Execute d'abord "
            "python -m ml.prediction.predict."
        )

    pipeline = joblib.load(BEST_MODEL_PATH)
    report = json.loads(PREDICTION_REPORT_PATH.read_text(encoding="utf-8"))

    return ModelBundle(
        pipeline=pipeline,
        model_name=report["model_name"],
        medium_threshold=report["medium_risk_threshold"],
        high_threshold=report["high_risk_threshold"],
    )
