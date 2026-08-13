"""
Feature Engineering (Etape 8).

Lit le Parquet Curated, calcule les variables derivees utiles aux KPIs,
aux Data Marts et au futur modele de Machine Learning, puis ecrit un
Parquet Features garde par encounter_id.
"""

import argparse
from pathlib import Path
from typing import Any

import polars as pl

from src.utils.logging_config import get_logger
from src.utils.paths import CURATED_DIR, FEATURES_DIR, create_required_directories

logger = get_logger("feature_engineering")

FEATURES_VERSION = "1.0.0"

MEDICATION_COLUMNS = (
    "metformin",
    "repaglinide",
    "nateglinide",
    "chlorpropamide",
    "glimepiride",
    "acetohexamide",
    "glipizide",
    "glyburide",
    "tolbutamide",
    "pioglitazone",
    "rosiglitazone",
    "acarbose",
    "miglitol",
    "troglitazone",
    "tolazamide",
    "examide",
    "citoglipton",
    "insulin",
    "glyburide_metformin",
    "glipizide_metformin",
    "glimepiride_pioglitazone",
    "metformin_rosiglitazone",
    "metformin_pioglitazone",
)

DIAGNOSIS_COLUMNS = ("diag_1", "diag_2", "diag_3")

AGE_MIDPOINTS: dict[str, int] = {
    "[0-10)": 5,
    "[10-20)": 15,
    "[20-30)": 25,
    "[30-40)": 35,
    "[40-50)": 45,
    "[50-60)": 55,
    "[60-70)": 65,
    "[70-80)": 75,
    "[80-90)": 85,
    "[90-100)": 95,
}

# Seuils pedagogiques documentes dans docs/data_dictionary_features.md.
# Ils servent aux KPIs et dashboards, pas au modele ML (Etape 17), qui
# utilise les variables continues brutes.
FREQUENT_PATIENT_MIN_PREVIOUS_VISITS = 3
HIGH_MEDICATION_BURDEN_MIN_MEDICATIONS = 15


def diagnosis_group_expr(column_name: str) -> pl.Expr:
    """
    Regrouper un code diagnostic ICD-9 en famille clinique.

    Le regroupement suit la classification utilisee dans la litterature
    de reference sur ce dataset (Strack et al., 2014) : Circulatory,
    Respiratory, Digestive, Diabetes, Injury, Musculoskeletal,
    Genitourinary, Neoplasms, Other. Les codes V/E et les codes non
    reconnus sont classes en Other.
    """
    raw = pl.col(column_name)

    numeric_code = (
        raw.str.extract(r"^(\d+)", 1)
        .cast(pl.Float64, strict=False)
    )

    is_diabetes = raw.str.starts_with("250")

    return (
        pl.when(raw.is_null())
        .then(pl.lit(None, dtype=pl.String))
        .when(is_diabetes)
        .then(pl.lit("Diabetes"))
        .when(numeric_code.is_between(390, 459) | (numeric_code == 785))
        .then(pl.lit("Circulatory"))
        .when(numeric_code.is_between(460, 519) | (numeric_code == 786))
        .then(pl.lit("Respiratory"))
        .when(numeric_code.is_between(520, 579) | (numeric_code == 787))
        .then(pl.lit("Digestive"))
        .when(numeric_code.is_between(800, 999))
        .then(pl.lit("Injury"))
        .when(numeric_code.is_between(710, 739))
        .then(pl.lit("Musculoskeletal"))
        .when(numeric_code.is_between(580, 629) | (numeric_code == 788))
        .then(pl.lit("Genitourinary"))
        .when(numeric_code.is_between(140, 239))
        .then(pl.lit("Neoplasms"))
        .otherwise(pl.lit("Other"))
        .alias(f"{column_name}_group")
    )


def resolve_curated_file(curated_path: Path | None = None) -> Path:
    """Trouver le fichier Curated a transformer."""
    if curated_path is not None:
        resolved_path = curated_path.resolve()

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Fichier Curated introuvable : {resolved_path}"
            )

        return resolved_path

    curated_files = list(CURATED_DIR.glob("*_curated.parquet"))

    if not curated_files:
        raise FileNotFoundError(
            "Aucun fichier Curated trouve dans data/curated. "
            "Execute d'abord l'etape 7 (Pipeline ETL)."
        )

    return max(
        curated_files,
        key=lambda path: path.stat().st_mtime,
    ).resolve()


def add_readmission_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Traduire la variable cible en indicateurs binaires exploitables."""
    return frame.with_columns(
        (pl.col("readmitted") == "<30")
        .cast(pl.Int8)
        .alias("readmitted_30_days"),
        (pl.col("readmitted") != "NO")
        .cast(pl.Int8)
        .alias("readmitted_flag"),
    )


def add_age_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Convertir la tranche d'age textuelle en point milieu numerique."""
    return frame.with_columns(
        pl.col("age")
        .replace_strict(AGE_MIDPOINTS, default=None, return_dtype=pl.Int32)
        .alias("age_midpoint")
    )


def add_utilization_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Calculer les indicateurs d'utilisation des soins."""
    total_previous_visits = (
        pl.col("number_outpatient")
        + pl.col("number_emergency")
        + pl.col("number_inpatient")
    )

    frame = frame.with_columns(
        total_previous_visits.alias("total_previous_visits"),
    )

    return frame.with_columns(
        (pl.col("total_previous_visits") + pl.col("time_in_hospital"))
        .alias("healthcare_utilization_score"),
        (pl.col("total_previous_visits") >= FREQUENT_PATIENT_MIN_PREVIOUS_VISITS)
        .cast(pl.Int8)
        .alias("is_frequent_patient"),
    )


def add_medication_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Calculer les indicateurs lies aux traitements medicamenteux."""
    active_medication_flags = [
        (pl.col(column) != "No").cast(pl.Int8)
        for column in MEDICATION_COLUMNS
    ]

    dosage_change_flags = [
        pl.col(column).is_in(["Up", "Down"]).cast(pl.Int8)
        for column in MEDICATION_COLUMNS
    ]

    frame = frame.with_columns(
        pl.sum_horizontal(active_medication_flags).alias(
            "active_medications_count"
        ),
        pl.sum_horizontal(dosage_change_flags).alias(
            "medication_dosage_changes_count"
        ),
        (pl.col("insulin") != "No").cast(pl.Int8).alias("insulin_prescribed"),
        (pl.col("num_medications") >= HIGH_MEDICATION_BURDEN_MIN_MEDICATIONS)
        .cast(pl.Int8)
        .alias("high_medication_burden_flag"),
    )

    return frame


def add_diagnosis_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Regrouper les diagnostics par famille clinique."""
    expressions = [
        diagnosis_group_expr(column_name)
        for column_name in DIAGNOSIS_COLUMNS
    ]

    return frame.with_columns(expressions)


def add_complexity_score(frame: pl.DataFrame) -> pl.DataFrame:
    """
    Calculer un score de complexite patient.

    Formule : num_medications + num_procedures + number_diagnoses
    + time_in_hospital. Un score eleve indique un sejour lourd, utile
    comme facteur explicatif du risque de reheospitalisation.
    """
    complexity_score = (
        pl.col("num_medications")
        + pl.col("num_procedures")
        + pl.col("number_diagnoses")
        + pl.col("time_in_hospital")
    )

    return frame.with_columns(
        complexity_score.alias("patient_complexity_score")
    )


def select_feature_columns(frame: pl.DataFrame) -> pl.DataFrame:
    """Conserver la cle metier et les seules colonnes derivees."""
    feature_columns = [
        "readmitted_30_days",
        "readmitted_flag",
        "age_midpoint",
        "total_previous_visits",
        "healthcare_utilization_score",
        "is_frequent_patient",
        "active_medications_count",
        "medication_dosage_changes_count",
        "insulin_prescribed",
        "high_medication_burden_flag",
        "diag_1_group",
        "diag_2_group",
        "diag_3_group",
        "patient_complexity_score",
    ]

    return frame.select(
        "encounter_id",
        "patient_nbr",
        *feature_columns,
    )


def validate_features_frame(frame: pl.DataFrame) -> None:
    """Effectuer les controles finaux sur la table de features."""
    if frame.height == 0:
        raise ValueError("Le resultat Features est vide.")

    if frame.get_column("encounter_id").null_count() > 0:
        raise ValueError("encounter_id contient des valeurs nulles.")

    encounter_count = frame.get_column("encounter_id").n_unique()

    if encounter_count != frame.height:
        raise ValueError("encounter_id n'est pas unique dans les Features.")

    binary_columns = (
        "readmitted_30_days",
        "readmitted_flag",
        "is_frequent_patient",
        "insulin_prescribed",
        "high_medication_burden_flag",
    )

    for column_name in binary_columns:
        invalid_rows = frame.filter(
            ~pl.col(column_name).is_in([0, 1])
        ).height

        if invalid_rows > 0:
            raise ValueError(
                f"{column_name} contient des valeurs hors {{0, 1}}."
            )


def build_feature_frame(
    frame: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Appliquer toutes les transformations de Feature Engineering."""
    input_rows = frame.height

    enriched = add_readmission_features(frame)
    enriched = add_age_features(enriched)
    enriched = add_utilization_features(enriched)
    enriched = add_medication_features(enriched)
    enriched = add_diagnosis_features(enriched)
    enriched = add_complexity_score(enriched)

    features = select_feature_columns(enriched)
    features = features.sort("encounter_id")

    validate_features_frame(features)

    statistics: dict[str, Any] = {
        "input_rows": input_rows,
        "output_rows": features.height,
        "output_columns": features.width,
        "readmitted_30_days_rate": round(
            float(features.get_column("readmitted_30_days").mean() or 0.0),
            4,
        ),
        "frequent_patient_rate": round(
            float(features.get_column("is_frequent_patient").mean() or 0.0),
            4,
        ),
        "insulin_prescribed_rate": round(
            float(features.get_column("insulin_prescribed").mean() or 0.0),
            4,
        ),
    }

    return features, statistics


def build_features_path(curated_file: Path) -> Path:
    """Construire le chemin du fichier Features."""
    base_name = curated_file.stem.removesuffix("_curated")

    return FEATURES_DIR / f"{base_name}_features.parquet"


def build_features_from_file(
    curated_path: Path | None = None,
) -> tuple[pl.DataFrame, Path, dict[str, Any]]:
    """Lire le fichier Curated, calculer les features et sauvegarder."""
    create_required_directories()

    curated_file = resolve_curated_file(curated_path)

    logger.info("Lecture du fichier Curated : %s", curated_file)

    frame = pl.read_parquet(curated_file)

    features, statistics = build_feature_frame(frame)

    features_path = build_features_path(curated_file)

    features.write_parquet(
        features_path,
        compression="zstd",
        statistics=True,
    )

    logger.info(
        "Fichier Features cree | lignes=%s | colonnes=%s | fichier=%s",
        features.height,
        features.width,
        features_path,
    )

    statistics["source_curated_path"] = str(curated_file)
    statistics["features_path"] = str(features_path.resolve())
    statistics["features_version"] = FEATURES_VERSION

    return features, features_path.resolve(), statistics


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description=(
            "Calculer les variables derivees (Feature Engineering) a "
            "partir du Parquet Curated."
        )
    )

    parser.add_argument(
        "--curated",
        type=Path,
        default=None,
        help=(
            "Chemin d'un fichier *_curated.parquet. Par defaut, le "
            "fichier le plus recent est utilise."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Lancer le Feature Engineering en ligne de commande."""
    arguments = parse_arguments()

    _, features_path, statistics = build_features_from_file(
        arguments.curated
    )

    print()
    print("RESULTAT DU FEATURE ENGINEERING")

    for key, value in statistics.items():
        print(f"{key}: {value}")

    print(f"features_path: {features_path}")


if __name__ == "__main__":
    main()
