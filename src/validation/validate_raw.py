import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl
from pandera.errors import SchemaError, SchemaErrors
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.utils.database import get_engine
from src.utils.logging_config import get_logger
from src.utils.paths import (
    CLEAN_DIR,
    QUARANTINE_DIR,
    RAW_DIR,
    ROOT_DIR,
    WAREHOUSE_DIR,
    create_required_directories,
)
from src.validation.schema import (
    CATEGORY_RULES,
    CRITICAL_COLUMNS,
    EXPECTED_COLUMNS,
    NUMERIC_RULES,
    RAW_DATA_SCHEMA,
)

logger = get_logger("data_quality")

REPORTS_DIR = ROOT_DIR / "reports" / "quality"
DOCUMENTATION_REPORT = ROOT_DIR / "docs" / "data_quality_report.md"


def resolve_raw_file(raw_path: Path | None = None) -> Path:
    """Trouver le fichier Raw à contrôler."""
    if raw_path is not None:
        resolved_path = raw_path.resolve()

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Fichier Raw introuvable : {resolved_path}"
            )

        return resolved_path

    raw_files = list(RAW_DIR.glob("*.parquet"))

    if not raw_files:
        raise FileNotFoundError(
            "Aucun fichier Parquet trouvé dans data/raw."
        )

    return max(
        raw_files,
        key=lambda path: path.stat().st_mtime,
    ).resolve()


def ensure_quality_tables(engine: Engine) -> None:
    """Créer les tables PostgreSQL de suivi qualité."""
    ddl_path = (
        WAREHOUSE_DIR
        / "ddl"
        / "002_create_data_quality_tables.sql"
    )

    if not ddl_path.exists():
        raise FileNotFoundError(
            f"Script SQL introuvable : {ddl_path}"
        )

    ddl_content = ddl_path.read_text(encoding="utf-8-sig")

    statements = [
        statement.strip()
        for statement in ddl_content.split(";")
        if statement.strip()
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)


def create_quality_run(
    engine: Engine,
    raw_file: Path,
) -> int:
    """Créer une exécution qualité avec le statut RUNNING."""
    query = text(
        """
        INSERT INTO data_quality_runs (
            raw_file_name,
            raw_path,
            status
        )
        VALUES (
            :raw_file_name,
            :raw_path,
            'RUNNING'
        )
        RETURNING id
        """
    )

    with engine.begin() as connection:
        run_id = connection.execute(
            query,
            {
                "raw_file_name": raw_file.name,
                "raw_path": str(raw_file),
            },
        ).scalar_one()

    return int(run_id)


def mark_quality_run_failed(
    engine: Engine,
    run_id: int,
    error_message: str,
) -> None:
    """Enregistrer l'échec du contrôle qualité."""
    query = text(
        """
        UPDATE data_quality_runs
        SET status = 'FAILED',
            error_message = :error_message,
            finished_at = CURRENT_TIMESTAMP
        WHERE id = :run_id
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "run_id": run_id,
                "error_message": error_message[:4000],
            },
        )


def mark_quality_run_success(
    engine: Engine,
    run_id: int,
    result: dict[str, Any],
    violation_summary: pl.DataFrame,
) -> None:
    """Enregistrer le résultat final et les erreurs par règle."""
    update_query = text(
        """
        UPDATE data_quality_runs
        SET status = 'SUCCESS',
            total_rows = :total_rows,
            valid_rows = :valid_rows,
            rejected_rows = :rejected_rows,
            total_violations = :total_violations,
            duplicate_rows = :duplicate_rows,
            valid_path = :valid_path,
            quarantine_path = :quarantine_path,
            report_path = :report_path,
            finished_at = CURRENT_TIMESTAMP
        WHERE id = :run_id
        """
    )

    violation_query = text(
        """
        INSERT INTO data_quality_rule_results (
            quality_run_id,
            rule_name,
            column_name,
            violation_count,
            description
        )
        VALUES (
            :quality_run_id,
            :rule_name,
            :column_name,
            :violation_count,
            :description
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(
            update_query,
            {
                "run_id": run_id,
                **result,
            },
        )

        for row in violation_summary.iter_rows(named=True):
            connection.execute(
                violation_query,
                {
                    "quality_run_id": run_id,
                    "rule_name": row["rule_name"],
                    "column_name": row["column_name"],
                    "violation_count": row["violation_count"],
                    "description": row["rejection_reason"],
                },
            )


def validate_required_schema(frame: pl.DataFrame) -> None:
    """Valider la présence des colonnes obligatoires."""
    missing_columns = sorted(
        set(EXPECTED_COLUMNS) - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            "Colonnes obligatoires absentes : "
            + ", ".join(missing_columns)
        )

    try:
        RAW_DATA_SCHEMA.validate(
            frame,
            lazy=True,
        )
    except (SchemaError, SchemaErrors) as error:
        raise ValueError(
            f"Le schéma Pandera est invalide : {error}"
        ) from error


def missing_expression(column_name: str) -> pl.Expr:
    """Identifier une valeur absente, vide ou représentée par ?."""
    text_value = (
        pl.col(column_name)
        .cast(pl.String, strict=False)
        .str.strip_chars()
    )

    return (
        pl.col(column_name).is_null()
        | text_value.is_in(["", "?"]).fill_null(False)
    )


def violation_frame(
    frame: pl.DataFrame,
    mask: pl.Expr | pl.Series,
    column_name: str,
    rule_name: str,
    reason: str,
    rejected_at: datetime,
    value_expression: pl.Expr | None = None,
) -> pl.DataFrame:
    """Créer les détails d'une violation."""
    if value_expression is None:
        invalid_value = (
            pl.col(column_name)
            .cast(pl.String, strict=False)
            .fill_null("<NULL>")
        )
    else:
        invalid_value = value_expression

    return frame.filter(mask).select(
        pl.col("__row_id"),
        pl.lit(rule_name).alias("rule_name"),
        pl.lit(column_name).alias("column_name"),
        invalid_value.alias("invalid_value"),
        pl.lit(reason).alias("rejection_reason"),
        pl.lit(rejected_at).alias("rejected_at"),
    )


def build_violations(frame: pl.DataFrame) -> pl.DataFrame:
    """Appliquer les règles techniques et métiers."""
    rejected_at = datetime.now(timezone.utc)
    violation_frames: list[pl.DataFrame] = []

    for column_name in dict.fromkeys(CRITICAL_COLUMNS):
        violation_frames.append(
            violation_frame(
                frame=frame,
                mask=missing_expression(column_name),
                column_name=column_name,
                rule_name="required_value",
                reason="La valeur obligatoire est absente.",
                rejected_at=rejected_at,
            )
        )

    for column_name, rule in NUMERIC_RULES.items():
        minimum, maximum, reason = rule

        numeric_value = pl.col(column_name).cast(
            pl.Int64,
            strict=False,
        )

        invalid_mask = (
            ~missing_expression(column_name)
            & (
                numeric_value.is_null()
                | (numeric_value < minimum)
            )
        )

        if maximum is not None:
            invalid_mask = invalid_mask | (
                ~missing_expression(column_name)
                & (numeric_value > maximum)
            )

        violation_frames.append(
            violation_frame(
                frame=frame,
                mask=invalid_mask,
                column_name=column_name,
                rule_name="invalid_numeric_value",
                reason=reason,
                rejected_at=rejected_at,
            )
        )

    for column_name, allowed_values in CATEGORY_RULES.items():
        text_value = (
            pl.col(column_name)
            .cast(pl.String, strict=False)
            .str.strip_chars()
        )

        invalid_mask = (
            ~missing_expression(column_name)
            & ~text_value.is_in(
                sorted(allowed_values)
            ).fill_null(False)
        )

        violation_frames.append(
            violation_frame(
                frame=frame,
                mask=invalid_mask,
                column_name=column_name,
                rule_name="invalid_category",
                reason=(
                    "La valeur ne fait pas partie "
                    "des catégories autorisées."
                ),
                rejected_at=rejected_at,
            )
        )

    encounter_duplicate_mask = (
        pl.col("encounter_id").is_duplicated()
        & ~missing_expression("encounter_id")
    )

    violation_frames.append(
        violation_frame(
            frame=frame,
            mask=encounter_duplicate_mask,
            column_name="encounter_id",
            rule_name="duplicate_encounter_id",
            reason=(
                "L'identifiant encounter_id doit être unique."
            ),
            rejected_at=rejected_at,
        )
    )

    exact_duplicate_mask = (
        frame
        .select(EXPECTED_COLUMNS)
        .is_duplicated()
    )

    violation_frames.append(
        violation_frame(
            frame=frame,
            mask=exact_duplicate_mask,
            column_name="*",
            rule_name="exact_duplicate_row",
            reason="La ligne est un doublon exact.",
            rejected_at=rejected_at,
            value_expression=pl.lit("<duplicate row>"),
        )
    )

    return pl.concat(
        violation_frames,
        how="vertical_relaxed",
    )


def build_missing_summary(
    frame: pl.DataFrame,
) -> pl.DataFrame:
    """Calculer les valeurs manquantes par colonne."""
    total_rows = frame.height
    results: list[dict[str, Any]] = []

    for column_name in frame.columns:
        missing_count = int(
            frame.select(
                missing_expression(column_name)
                .sum()
                .alias("missing_count")
            ).item()
        )

        missing_rate = (
            (missing_count / total_rows) * 100
            if total_rows
            else 0.0
        )

        results.append(
            {
                "column_name": column_name,
                "missing_count": missing_count,
                "missing_rate_percent": round(
                    missing_rate,
                    4,
                ),
            }
        )

    return (
        pl.DataFrame(results)
        .sort(
            "missing_count",
            descending=True,
        )
    )


def dataframe_to_markdown(
    frame: pl.DataFrame,
) -> str:
    """Transformer un petit DataFrame en tableau Markdown."""
    if frame.height == 0:
        return "_Aucune anomalie détectée._"

    headers = frame.columns
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for row in frame.iter_rows():
        values = [
            str(value).replace("|", "/")
            for value in row
        ]
        lines.append(
            "| " + " | ".join(values) + " |"
        )

    return "\n".join(lines)


def write_quality_reports(
    raw_file: Path,
    result: dict[str, Any],
    frame: pl.DataFrame,
    missing_summary: pl.DataFrame,
    violation_summary: pl.DataFrame,
) -> dict[str, str]:
    """Créer les rapports JSON, CSV et Markdown."""
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    DOCUMENTATION_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        REPORTS_DIR
        / "quality_report_latest.json"
    )
    missing_csv_path = (
        REPORTS_DIR
        / "missing_values_latest.csv"
    )
    violations_csv_path = (
        REPORTS_DIR
        / "violation_summary_latest.csv"
    )

    payload = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "raw_file": str(raw_file),
        "summary": {
            "total_rows": result["total_rows"],
            "valid_rows": result["valid_rows"],
            "rejected_rows": result["rejected_rows"],
            "total_violations": result["total_violations"],
            "duplicate_rows": result["duplicate_rows"],
            "valid_rate_percent": result[
                "valid_rate_percent"
            ],
        },
        "column_types": {
            name: str(dtype)
            for name, dtype in frame.schema.items()
        },
        "violations": violation_summary.to_dicts(),
        "missing_values": missing_summary.to_dicts(),
    }

    json_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    missing_summary.write_csv(missing_csv_path)
    violation_summary.write_csv(violations_csv_path)

    markdown_content = f"""# Rapport automatique de qualité des données

## Informations générales

- Fichier contrôlé : `{raw_file.name}`
- Date du contrôle : `{payload["generated_at"]}`
- Nombre total de lignes : **{result["total_rows"]}**
- Lignes valides : **{result["valid_rows"]}**
- Lignes rejetées : **{result["rejected_rows"]}**
- Nombre total de violations : **{result["total_violations"]}**
- Doublons exacts : **{result["duplicate_rows"]}**
- Taux de lignes valides : **{result["valid_rate_percent"]}%**

## Résultat du contrôle

Les lignes valides sont enregistrées dans :

`{result["valid_path"]}`

Les lignes rejetées sont enregistrées dans :

`{result["quarantine_path"]}`

## Violations détectées

{dataframe_to_markdown(violation_summary)}

## Colonnes avec le plus de valeurs manquantes

{dataframe_to_markdown(missing_summary.head(15))}

## Interprétation

Une valeur `?`, une chaîne vide ou une valeur nulle est comptée comme
manquante. Les valeurs manquantes des colonnes facultatives sont signalées
dans le rapport, mais ne provoquent pas automatiquement le rejet d'une ligne.

Les lignes rejetées pourront être corrigées ou traitées durant le pipeline
ETL. Les données de la Raw Layer ne sont jamais modifiées.
"""

    DOCUMENTATION_REPORT.write_text(
        markdown_content,
        encoding="utf-8",
    )

    return {
        "report_path": str(DOCUMENTATION_REPORT),
        "json_report_path": str(json_path),
        "missing_csv_path": str(missing_csv_path),
        "violations_csv_path": str(
            violations_csv_path
        ),
    }


def validate_raw_data(
    raw_path: Path | None = None,
) -> dict[str, Any]:
    """Exécuter le pipeline complet de qualité."""
    create_required_directories()
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_file = resolve_raw_file(raw_path)

    engine = get_engine()
    ensure_quality_tables(engine)

    run_id = create_quality_run(
        engine,
        raw_file,
    )

    logger.info(
        "Début du contrôle qualité run_id=%s | fichier=%s",
        run_id,
        raw_file,
    )

    try:
        frame = pl.read_parquet(raw_file)

        if frame.height == 0:
            raise ValueError(
                "Le fichier Raw ne contient aucune ligne."
            )

        validate_required_schema(frame)

        indexed_frame = frame.with_row_index(
            "__row_id"
        )

        violations = build_violations(
            indexed_frame
        )

        invalid_row_ids = (
            violations
            .select("__row_id")
            .unique()
        )

        valid_frame = (
            indexed_frame
            .join(
                invalid_row_ids,
                on="__row_id",
                how="anti",
            )
            .drop("__row_id")
        )

        quarantine_frame = (
            violations
            .join(
                indexed_frame,
                on="__row_id",
                how="left",
            )
            .select(
                "__row_id",
                "rule_name",
                "column_name",
                "invalid_value",
                "rejection_reason",
                "rejected_at",
                *EXPECTED_COLUMNS,
            )
        )

        valid_path = (
            CLEAN_DIR
            / f"{raw_file.stem}_validated.parquet"
        )

        quarantine_path = (
            QUARANTINE_DIR
            / f"{raw_file.stem}_rejected.parquet"
        )

        valid_frame.write_parquet(
            valid_path,
            compression="zstd",
            statistics=True,
        )

        quarantine_frame.write_parquet(
            quarantine_path,
            compression="zstd",
            statistics=True,
        )

        violation_summary = (
            violations
            .group_by(
                "rule_name",
                "column_name",
                "rejection_reason",
            )
            .len()
            .rename(
                {
                    "len": "violation_count",
                }
            )
            .sort(
                "violation_count",
                descending=True,
            )
        )

        missing_summary = build_missing_summary(
            frame
        )

        duplicate_rows = (
            violations
            .filter(
                pl.col("rule_name")
                == "exact_duplicate_row"
            )
            .get_column("__row_id")
            .n_unique()
            if violations.height
            else 0
        )

        valid_rate = (
            (valid_frame.height / frame.height) * 100
            if frame.height
            else 0.0
        )

        result: dict[str, Any] = {
            "run_id": run_id,
            "status": "SUCCESS",
            "raw_file": str(raw_file),
            "total_rows": frame.height,
            "valid_rows": valid_frame.height,
            "rejected_rows": invalid_row_ids.height,
            "total_violations": violations.height,
            "duplicate_rows": int(duplicate_rows),
            "valid_rate_percent": round(
                valid_rate,
                4,
            ),
            "valid_path": str(
                valid_path.resolve()
            ),
            "quarantine_path": str(
                quarantine_path.resolve()
            ),
        }

        report_paths = write_quality_reports(
            raw_file=raw_file,
            result=result,
            frame=frame,
            missing_summary=missing_summary,
            violation_summary=violation_summary,
        )

        result.update(report_paths)

        mark_quality_run_success(
            engine=engine,
            run_id=run_id,
            result=result,
            violation_summary=violation_summary,
        )

        logger.info(
            "Contrôle réussi | total=%s | valides=%s | "
            "rejetées=%s | violations=%s",
            result["total_rows"],
            result["valid_rows"],
            result["rejected_rows"],
            result["total_violations"],
        )

        return result

    except Exception as error:
        mark_quality_run_failed(
            engine=engine,
            run_id=run_id,
            error_message=str(error),
        )

        logger.exception(
            "Échec du contrôle qualité run_id=%s : %s",
            run_id,
            error,
        )

        raise


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments du terminal."""
    parser = argparse.ArgumentParser(
        description=(
            "Contrôler un fichier Raw et séparer "
            "les données valides et invalides."
        )
    )

    parser.add_argument(
        "--raw",
        type=Path,
        default=None,
        help=(
            "Chemin du fichier Parquet. "
            "Par défaut, le plus récent est utilisé."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Lancer le contrôle qualité."""
    arguments = parse_arguments()

    result = validate_raw_data(
        arguments.raw
    )

    print()
    print("RESULTAT DU CONTROLE QUALITE")

    keys_to_display = (
        "run_id",
        "status",
        "total_rows",
        "valid_rows",
        "rejected_rows",
        "total_violations",
        "duplicate_rows",
        "valid_rate_percent",
        "valid_path",
        "quarantine_path",
        "report_path",
    )

    for key in keys_to_display:
        print(f"{key}: {result[key]}")


if __name__ == "__main__":
    main()