"""
Entrainement et comparaison des modeles predictifs (Etape 17).

Compare Logistic Regression, Random Forest et XGBoost pour predire
readmitted_30_days a partir des tables staging (Curated + Features),
journalise chaque run dans MLflow et sauvegarde le meilleur pipeline
(pretraitement + modele) dans ml/models/.
"""

import argparse
import json
from datetime import datetime, timezone
from typing import Any

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from ml.evaluation.metrics import compute_classification_metrics
from src.utils.database import get_engine
from src.utils.logging_config import get_logger
from src.utils.paths import MODELS_DIR, ROOT_DIR, create_required_directories

logger = get_logger("ml_training")

MLFLOW_EXPERIMENT_NAME = "hospital_readmission_30_days"

ML_REPORTS_DIR = ROOT_DIR / "reports" / "ml"

# Codes discharge_disposition_id correspondant a un deces ou une sortie
# en hospice (voir data/source/IDS_mapping.csv). Ces sejours sont
# exclus de l'entrainement : un patient decede ne peut pas etre
# reheospitalise, ce qui biaiserait le modele (pratique standard sur ce
# dataset, cf. litterature de reference Strack et al., 2014).
EXCLUDED_DISCHARGE_DISPOSITION_IDS = (11, 13, 14, 19, 20, 21)

NUMERIC_FEATURES = (
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_diagnoses",
    "age_midpoint",
    "total_previous_visits",
    "healthcare_utilization_score",
    "patient_complexity_score",
    "active_medications_count",
    "medication_dosage_changes_count",
)

CATEGORICAL_FEATURES = (
    "gender",
    "race",
    "admission_type_id",
    "discharge_disposition_id",
    "admission_source_id",
    "max_glu_serum",
    "a1c_result",
    "change",
    "diabetesmed",
    "insulin_prescribed",
    "diag_1_group",
)

TARGET_COLUMN = "readmitted_30_days"

TRAINING_QUERY = f"""
    SELECT
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
        f.diag_1_group,
        f.readmitted_30_days
    FROM staging.hospital_encounters_curated c
    JOIN staging.hospital_encounters_features f
        ON f.encounter_id = c.encounter_id
    WHERE c.discharge_disposition_id NOT IN
        {EXCLUDED_DISCHARGE_DISPOSITION_IDS}
"""


def load_training_data(engine: Any) -> pd.DataFrame:
    """Charger le jeu d'entrainement depuis PostgreSQL."""
    frame = pd.read_sql(TRAINING_QUERY, engine)

    for column_name in CATEGORICAL_FEATURES:
        frame[column_name] = frame[column_name].astype(str)

    return frame


def build_preprocessor() -> ColumnTransformer:
    """Construire le pretraitement commun a tous les modeles."""
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), list(NUMERIC_FEATURES)),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                list(CATEGORICAL_FEATURES),
            ),
        ]
    )


def build_candidate_models(
    positive_weight_ratio: float,
) -> dict[str, Any]:
    """Construire les trois modeles a comparer."""
    return {
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "xgboost": XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            eval_metric="logloss",
            scale_pos_weight=positive_weight_ratio,
            random_state=42,
            n_jobs=-1,
        ),
    }


def train_and_evaluate_model(
    model_name: str,
    model: Any,
    preprocessor: ColumnTransformer,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[Pipeline, dict[str, Any]]:
    """Entrainer un modele, l'evaluer et journaliser le run dans MLflow."""
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    with mlflow.start_run(run_name=model_name):
        pipeline.fit(x_train, y_train)

        y_pred = pipeline.predict(x_test)
        y_proba = pipeline.predict_proba(x_test)[:, 1]

        metrics = compute_classification_metrics(y_test, y_pred, y_proba)

        mlflow.log_param("model_name", model_name)
        mlflow.log_params(
            {
                key: value
                for key, value in model.get_params().items()
                if isinstance(value, (int, float, str, bool)) or value is None
            }
        )
        mlflow.log_metrics(
            {
                key: value
                for key, value in metrics.items()
                if isinstance(value, (int, float))
            }
        )
        mlflow.sklearn.log_model(pipeline, artifact_path="model")

    logger.info(
        "Modele entraine | modele=%s | roc_auc=%s | f1=%s",
        model_name,
        metrics["roc_auc"],
        metrics["f1_score"],
    )

    return pipeline, metrics


def train_models() -> dict[str, Any]:
    """Entrainer, comparer et sauvegarder le meilleur modele."""
    create_required_directories()
    ML_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    logger.info("Chargement du jeu d'entrainement")

    data = load_training_data(get_engine())

    x = data[list(NUMERIC_FEATURES) + list(CATEGORICAL_FEATURES)]
    y = data[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        stratify=y,
        random_state=42,
    )

    positive_weight_ratio = (
        (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    )

    candidates = build_candidate_models(positive_weight_ratio)

    results: dict[str, dict[str, Any]] = {}
    pipelines: dict[str, Pipeline] = {}

    for model_name, model in candidates.items():
        pipeline, metrics = train_and_evaluate_model(
            model_name=model_name,
            model=model,
            preprocessor=build_preprocessor(),
            x_train=x_train,
            y_train=y_train,
            x_test=x_test,
            y_test=y_test,
        )

        results[model_name] = metrics
        pipelines[model_name] = pipeline

    best_model_name = max(
        results,
        key=lambda name: results[name]["roc_auc"],
    )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    best_model_path = MODELS_DIR / "best_model.joblib"

    joblib.dump(pipelines[best_model_name], best_model_path)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "training_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "positive_rate": round(float(y.mean()), 4),
        "best_model": best_model_name,
        "best_model_path": str(best_model_path.resolve()),
        "results": results,
        "numeric_features": list(NUMERIC_FEATURES),
        "categorical_features": list(CATEGORICAL_FEATURES),
        "excluded_discharge_disposition_ids": list(
            EXCLUDED_DISCHARGE_DISPOSITION_IDS
        ),
    }

    report_path = ML_REPORTS_DIR / "model_evaluation_latest.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report["report_path"] = str(report_path.resolve())

    logger.info(
        "Entrainement termine | meilleur modele=%s | roc_auc=%s",
        best_model_name,
        results[best_model_name]["roc_auc"],
    )

    return report


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments de la ligne de commande."""
    return argparse.ArgumentParser(
        description=(
            "Entrainer et comparer les modeles de prediction de "
            "reheospitalisation a 30 jours."
        )
    ).parse_args()


def main() -> None:
    """Lancer l'entrainement des modeles."""
    parse_arguments()

    report = train_models()

    print()
    print("RESULTAT DE L'ENTRAINEMENT DES MODELES")
    print(f"best_model: {report['best_model']}")
    print(f"training_rows: {report['training_rows']}")
    print(f"test_rows: {report['test_rows']}")

    for model_name, metrics in report["results"].items():
        print(f"\n{model_name}:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
