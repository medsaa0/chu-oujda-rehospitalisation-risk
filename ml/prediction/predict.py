"""
Pipeline de prediction du risque de reheospitalisation (Etape 17).

Charge le meilleur modele sauvegarde par ml/training/train_models.py,
score les hospitalisations et ecrit les resultats dans
warehouse.fact_prediction.
"""

import argparse
import json
from datetime import datetime, timezone
from typing import Any

import joblib
import pandas as pd

from ml.training.train_models import (
    CATEGORICAL_FEATURES,
    EXCLUDED_DISCHARGE_DISPOSITION_IDS,
    NUMERIC_FEATURES,
)
from src.loading.load_postgres import execute_sql_script
from src.utils.database import get_engine
from src.utils.logging_config import get_logger
from src.utils.paths import MODELS_DIR, ROOT_DIR, WAREHOUSE_DIR

logger = get_logger("ml_prediction")

BEST_MODEL_PATH = MODELS_DIR / "best_model.joblib"
MODEL_EVALUATION_REPORT_PATH = (
    ROOT_DIR / "reports" / "ml" / "model_evaluation_latest.json"
)

MEDIUM_RISK_QUANTILE = 0.80
HIGH_RISK_QUANTILE = 0.95

SCORING_QUERY = f"""
    SELECT
        c.encounter_id,
        c.gender,
        c.race,
        c.admission_type_id,
        c.discharge_disposition_id,
        c.admission_source_id,
        c.time_in_hospital,
        c.num_lab_procedures,
        c.num_procedures,
        c.num_medications,
        c.number_diagnoses,
        c.max_glu_serum,
        c.a1c_result,
        c.change,
        c.diabetesmed,
        f.age_midpoint,
        f.total_previous_visits,
        f.healthcare_utilization_score,
        f.patient_complexity_score,
        f.active_medications_count,
        f.medication_dosage_changes_count,
        f.insulin_prescribed,
        f.diag_1_group
    FROM staging.hospital_encounters_curated c
    JOIN staging.hospital_encounters_features f
        ON f.encounter_id = c.encounter_id
    WHERE c.discharge_disposition_id NOT IN
        {EXCLUDED_DISCHARGE_DISPOSITION_IDS}
"""


def load_model_metadata() -> dict[str, Any]:
    """Lire le rapport d'evaluation pour connaitre le modele retenu."""
    if not MODEL_EVALUATION_REPORT_PATH.exists():
        raise FileNotFoundError(
            "Aucun rapport d'evaluation trouve. "
            "Execute d'abord python -m ml.training.train_models."
        )

    return json.loads(
        MODEL_EVALUATION_REPORT_PATH.read_text(encoding="utf-8")
    )


def categorize_risk(
    probability: float,
    medium_threshold: float,
    high_threshold: float,
) -> str:
    """
    Traduire une probabilite en categorie de risque, par quantile.

    Les probabilites issues de class_weight='balanced' / scale_pos_weight
    ne sont pas calibrees (elles servent au classement, pas a une
    probabilite absolue fiable). On categorise donc par quantile de la
    population scoree plutot que par seuil de probabilite fixe : les
    MEDIUM_RISK_QUANTILE % les moins a risque sont "Low", les suivants
    jusqu'a HIGH_RISK_QUANTILE % sont "Medium", le reste "High".
    """
    if probability < medium_threshold:
        return "Low"

    if probability < high_threshold:
        return "Medium"

    return "High"


def load_scoring_data(engine: Any) -> pd.DataFrame:
    """Charger les hospitalisations a scorer depuis PostgreSQL."""
    frame = pd.read_sql(SCORING_QUERY, engine)

    for column_name in CATEGORICAL_FEATURES:
        frame[column_name] = frame[column_name].astype(str)

    return frame


def ensure_fact_prediction_table(engine: Any) -> None:
    """Creer warehouse.fact_prediction si necessaire."""
    execute_sql_script(
        engine,
        WAREHOUSE_DIR / "ddl" / "007_create_fact_prediction.sql",
    )


def write_predictions_to_postgres(
    engine: Any,
    predictions: pd.DataFrame,
) -> int:
    """Remplacer le contenu de warehouse.fact_prediction."""
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE TABLE warehouse.fact_prediction"
        )

        predictions.to_sql(
            name="fact_prediction",
            con=connection,
            schema="warehouse",
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi",
        )

        row_count = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM warehouse.fact_prediction"
        ).scalar_one()

    return int(row_count)


def run_predictions() -> dict[str, Any]:
    """Scorer toutes les hospitalisations et sauvegarder les resultats."""
    if not BEST_MODEL_PATH.exists():
        raise FileNotFoundError(
            "Aucun modele sauvegarde. "
            "Execute d'abord python -m ml.training.train_models."
        )

    metadata = load_model_metadata()
    pipeline = joblib.load(BEST_MODEL_PATH)

    engine = get_engine()

    logger.info("Chargement des donnees a scorer")

    data = load_scoring_data(engine)

    feature_columns = list(NUMERIC_FEATURES) + list(CATEGORICAL_FEATURES)
    probabilities = pipeline.predict_proba(data[feature_columns])[:, 1]

    medium_threshold = float(
        pd.Series(probabilities).quantile(MEDIUM_RISK_QUANTILE)
    )
    high_threshold = float(
        pd.Series(probabilities).quantile(HIGH_RISK_QUANTILE)
    )

    predictions = pd.DataFrame(
        {
            "encounter_key": data["encounter_id"],
            "predicted_probability": probabilities,
            "predicted_risk_category": [
                categorize_risk(probability, medium_threshold, high_threshold)
                for probability in probabilities
            ],
            "model_name": metadata["best_model"],
            "model_version": datetime.now(timezone.utc).isoformat(),
            "predicted_at": datetime.now(timezone.utc),
        }
    )

    ensure_fact_prediction_table(engine)

    row_count = write_predictions_to_postgres(engine, predictions)

    result = {
        "status": "SUCCESS",
        "model_name": metadata["best_model"],
        "scored_rows": int(len(predictions)),
        "postgres_row_count": row_count,
        "medium_risk_threshold": round(medium_threshold, 4),
        "high_risk_threshold": round(high_threshold, 4),
        "risk_distribution": (
            predictions["predicted_risk_category"]
            .value_counts()
            .to_dict()
        ),
    }

    logger.info(
        "Predictions ecrites | modele=%s | lignes=%s | repartition=%s",
        result["model_name"],
        result["scored_rows"],
        result["risk_distribution"],
    )

    return result


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments de la ligne de commande."""
    return argparse.ArgumentParser(
        description=(
            "Scorer les hospitalisations avec le meilleur modele et "
            "ecrire les resultats dans warehouse.fact_prediction."
        )
    ).parse_args()


def main() -> None:
    """Lancer le scoring."""
    parse_arguments()

    result = run_predictions()

    print()
    print("RESULTAT DU SCORING")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
