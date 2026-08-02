from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import polars as pl

from src.utils.logging_config import get_logger
from src.utils.paths import CLEAN_DIR, CURATED_DIR, create_required_directories
from src.validation.schema import (
    EXPECTED_COLUMNS,
    MEDICATION_COLUMNS,
    NUMERIC_RULES,
)

logger = get_logger("etl_transformation")

ETL_VERSION = "1.0.0"

NUMERIC_COLUMNS = tuple(NUMERIC_RULES.keys())

DIAGNOSIS_COLUMNS = (
    "diag_1",
    "diag_2",
    "diag_3",
)

UNKNOWN_VALUE_COLUMNS = (
    "race",
    "weight",
    "payer_code",
    "medical_specialty",
)

COLUMN_RENAMES = {
    column: column.replace("-", "_").lower()
    for column in EXPECTED_COLUMNS
}

COLUMN_RENAMES["A1Cresult"] = "a1c_result"

TECHNICAL_COLUMNS = (
    "etl_processed_at",
    "etl_source_file",
    "etl_version",
)


def resolve_clean_file(
    clean_path: Path | None = None,
) -> Path:
    """Trouver le fichier validé à transformer."""
    if clean_path is not None:
        resolved_path = clean_path.resolve()

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Fichier Clean introuvable : {resolved_path}"
            )

        if resolved_path.suffix.lower() != ".parquet":
            raise ValueError(
                "Le fichier Clean doit être au format Parquet."
            )

        return resolved_path

    clean_files = list(
        CLEAN_DIR.glob("*_validated.parquet")
    )

    if not clean_files:
        raise FileNotFoundError(
            "Aucun fichier validé trouvé dans data/clean. "
            "Exécute d'abord l'étape 6."
        )

    return max(
        clean_files,
        key=lambda path: path.stat().st_mtime,
    ).resolve()


def validate_input_columns(
    frame: pl.DataFrame,
) -> None:
    """Vérifier les colonnes avant transformation."""
    missing_columns = sorted(
        set(EXPECTED_COLUMNS) - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            "Colonnes manquantes dans le fichier Clean : "
            + ", ".join(missing_columns)
        )

    if frame.height == 0:
        raise ValueError(
            "Le fichier Clean ne contient aucune ligne."
        )


def select_expected_columns(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    """Conserver uniquement les colonnes métier attendues."""
    return frame.select(EXPECTED_COLUMNS)


def normalize_missing_values(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    """
    Transformer les chaînes vides et le caractère ? en valeurs nulles.

    Toutes les colonnes sont d'abord converties en texte, puis les colonnes
    numériques sont converties vers leur vrai type dans une étape suivante.
    """
    expressions: list[pl.Expr] = []

    for column_name in frame.columns:
        text_value = (
            pl.col(column_name)
            .cast(pl.String, strict=False)
            .str.strip_chars()
        )

        expression = (
            pl.when(
                text_value.is_in(["", "?"]).fill_null(False)
            )
            .then(
                pl.lit(
                    None,
                    dtype=pl.String,
                )
            )
            .otherwise(text_value)
            .alias(column_name)
        )

        expressions.append(expression)

    return frame.with_columns(expressions)


def remove_residual_duplicates(
    frame: pl.DataFrame,
) -> tuple[pl.DataFrame, int]:
    """
    Supprimer les doublons exacts et les encounter_id répétés.

    La validation de l'étape 6 doit déjà avoir retiré ces cas, mais ce contrôle
    supplémentaire rend le pipeline ETL plus robuste et idempotent.
    """
    input_rows = frame.height

    deduplicated_frame = frame.unique(
        maintain_order=True,
    )

    deduplicated_frame = deduplicated_frame.unique(
        subset=["encounter_id"],
        keep="first",
        maintain_order=True,
    )

    duplicates_removed = (
        input_rows - deduplicated_frame.height
    )

    return deduplicated_frame, duplicates_removed


def cast_numeric_columns(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    """Convertir les colonnes numériques en entiers 64 bits."""
    expressions = [
        pl.col(column_name)
        .cast(pl.Int64, strict=True)
        .alias(column_name)
        for column_name in NUMERIC_COLUMNS
    ]

    return frame.with_columns(expressions)


def fill_descriptive_unknown_values(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    """
    Remplacer les valeurs descriptives absentes par Unknown.

    Les diagnostics absents restent nulls, car inventer un diagnostic serait
    incorrect.
    """
    expressions = [
        pl.col(column_name)
        .fill_null("Unknown")
        .alias(column_name)
        for column_name in UNKNOWN_VALUE_COLUMNS
    ]

    return frame.with_columns(expressions)


def normalize_diagnosis_codes(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    """Nettoyer les espaces et normaliser les lettres des diagnostics."""
    expressions = [
        pl.col(column_name)
        .cast(pl.String, strict=False)
        .str.strip_chars()
        .str.to_uppercase()
        .alias(column_name)
        for column_name in DIAGNOSIS_COLUMNS
    ]

    return frame.with_columns(expressions)


def normalize_medication_columns(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    """Conserver les états des médicaments dans un format texte uniforme."""
    expressions = [
        pl.col(column_name)
        .cast(pl.String, strict=False)
        .str.strip_chars()
        .alias(column_name)
        for column_name in MEDICATION_COLUMNS
    ]

    return frame.with_columns(expressions)


def normalize_column_names(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    """
    Transformer les noms de colonnes en noms adaptés à PostgreSQL.

    Exemple :
    glyburide-metformin devient glyburide_metformin.
    A1Cresult devient a1c_result.
    """
    return frame.rename(COLUMN_RENAMES)


def add_technical_metadata(
    frame: pl.DataFrame,
    source_file_name: str,
) -> pl.DataFrame:
    """Ajouter les informations techniques de traitement."""
    processed_at = datetime.now(timezone.utc)

    return frame.with_columns(
        pl.lit(processed_at).alias(
            "etl_processed_at"
        ),
        pl.lit(source_file_name).alias(
            "etl_source_file"
        ),
        pl.lit(ETL_VERSION).alias(
            "etl_version"
        ),
    )


def order_curated_columns(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    """Organiser les colonnes métier puis les métadonnées ETL."""
    business_columns = [
        COLUMN_RENAMES.get(column, column)
        for column in EXPECTED_COLUMNS
    ]

    return frame.select(
        *business_columns,
        *TECHNICAL_COLUMNS,
    )


def validate_curated_frame(
    frame: pl.DataFrame,
) -> None:
    """Effectuer les contrôles finaux avant sauvegarde."""
    if frame.height == 0:
        raise ValueError(
            "Le résultat Curated est vide."
        )

    if frame.get_column(
        "encounter_id"
    ).null_count() > 0:
        raise ValueError(
            "encounter_id contient des valeurs nulles."
        )

    encounter_count = frame.get_column(
        "encounter_id"
    ).n_unique()

    if encounter_count != frame.height:
        raise ValueError(
            "encounter_id n'est pas unique dans le résultat Curated."
        )

    for column_name in NUMERIC_COLUMNS:
        if frame.schema[column_name] != pl.Int64:
            raise TypeError(
                f"{column_name} n'est pas de type Int64."
            )

    for column_name, data_type in frame.schema.items():
        if data_type != pl.String:
            continue

        question_mark_rows = frame.filter(
            pl.col(column_name).str.strip_chars() == "?"
        ).height

        if question_mark_rows > 0:
            raise ValueError(
                f"La colonne {column_name} contient encore des ?."
            )


def calculate_null_count(
    frame: pl.DataFrame,
) -> int:
    """Calculer le nombre total de valeurs nulles."""
    if not frame.columns:
        return 0

    null_counts = frame.null_count().row(0)

    return int(sum(null_counts))


def transform_dataframe(
    frame: pl.DataFrame,
    source_file_name: str,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Appliquer toutes les transformations métier et techniques."""
    validate_input_columns(frame)

    input_rows = frame.height
    source_columns = frame.width
    null_values_before = calculate_null_count(frame)

    transformed = select_expected_columns(frame)

    transformed = normalize_missing_values(
        transformed
    )

    transformed, duplicates_removed = (
        remove_residual_duplicates(
            transformed
        )
    )

    transformed = cast_numeric_columns(
        transformed
    )

    transformed = fill_descriptive_unknown_values(
        transformed
    )

    transformed = normalize_diagnosis_codes(
        transformed
    )

    transformed = normalize_medication_columns(
        transformed
    )

    transformed = normalize_column_names(
        transformed
    )

    transformed = add_technical_metadata(
        transformed,
        source_file_name=source_file_name,
    )

    transformed = order_curated_columns(
        transformed
    )

    transformed = transformed.sort(
        "encounter_id"
    )

    validate_curated_frame(
        transformed
    )

    statistics: dict[str, Any] = {
        "input_rows": input_rows,
        "output_rows": transformed.height,
        "duplicates_removed": duplicates_removed,
        "source_columns": source_columns,
        "output_columns": transformed.width,
        "null_values_before": null_values_before,
        "null_values_after": calculate_null_count(
            transformed
        ),
    }

    return transformed, statistics


def build_curated_path(
    clean_file: Path,
) -> Path:
    """Construire le chemin du fichier Curated."""
    base_name = clean_file.stem.removesuffix(
        "_validated"
    )

    return (
        CURATED_DIR
        / f"{base_name}_curated.parquet"
    )


def transform_clean_file(
    clean_path: Path | None = None,
) -> tuple[pl.DataFrame, Path, dict[str, Any]]:
    """Lire le fichier Clean, le transformer et créer le Parquet Curated."""
    create_required_directories()

    clean_file = resolve_clean_file(
        clean_path
    )

    logger.info(
        "Lecture du fichier Clean : %s",
        clean_file,
    )

    frame = pl.read_parquet(
        clean_file
    )

    transformed, statistics = transform_dataframe(
        frame=frame,
        source_file_name=clean_file.name,
    )

    curated_path = build_curated_path(
        clean_file
    )

    transformed.write_parquet(
        curated_path,
        compression="zstd",
        statistics=True,
    )

    logger.info(
        "Fichier Curated créé | lignes=%s | colonnes=%s | fichier=%s",
        transformed.height,
        transformed.width,
        curated_path,
    )

    statistics["source_clean_path"] = str(
        clean_file
    )
    statistics["curated_path"] = str(
        curated_path.resolve()
    )

    return transformed, curated_path.resolve(), statistics


def verify_parquet_with_duckdb(
    curated_path: Path,
) -> dict[str, int]:
    """Vérifier le Parquet Curated avec DuckDB."""
    parquet_path = (
        curated_path
        .resolve()
        .as_posix()
        .replace("'", "''")
    )

    query = f"""
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT encounter_id) AS distinct_encounter_count
        FROM read_parquet('{parquet_path}')
    """

    with duckdb.connect(
        database=":memory:"
    ) as connection:
        row_count, distinct_count = (
            connection.execute(query).fetchone()
        )

    row_count = int(row_count)
    distinct_count = int(distinct_count)

    if row_count == 0:
        raise ValueError(
            "DuckDB indique que le fichier Curated est vide."
        )

    if row_count != distinct_count:
        raise ValueError(
            "DuckDB a détecté des encounter_id dupliqués."
        )

    logger.info(
        "Vérification DuckDB réussie | lignes=%s | encounters=%s",
        row_count,
        distinct_count,
    )

    return {
        "duckdb_row_count": row_count,
        "duckdb_distinct_encounter_count": distinct_count,
    }