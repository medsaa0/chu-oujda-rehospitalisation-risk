import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.loading.load_postgres import (
    DEFAULT_TARGET_SCHEMA,
    DEFAULT_TARGET_TABLE,
    create_etl_run,
    ensure_etl_tracking_tables,
    load_dataframe_to_postgres,
    mark_etl_run_failed,
    mark_etl_run_success,
)
from src.transformation.transform_clean import (
    resolve_clean_file,
    transform_clean_file,
    verify_parquet_with_duckdb,
)
from src.utils.database import get_engine
from src.utils.logging_config import get_logger
from src.utils.paths import ROOT_DIR, create_required_directories

logger = get_logger("etl_pipeline")

ETL_REPORTS_DIR = (
    ROOT_DIR
    / "reports"
    / "etl"
)


def write_etl_report(
    result: dict[str, Any],
) -> Path:
    """Créer le rapport JSON de la dernière exécution ETL."""
    ETL_REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        ETL_REPORTS_DIR
        / "etl_report_latest.json"
    )

    report_path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return report_path.resolve()


def run_etl(
    clean_path: Path | None = None,
    target_schema: str = DEFAULT_TARGET_SCHEMA,
    target_table: str = DEFAULT_TARGET_TABLE,
) -> dict[str, Any]:
    """Exécuter Extraction, Transformation et Chargement."""
    create_required_directories()

    clean_file = resolve_clean_file(
        clean_path
    )

    engine = get_engine()

    ensure_etl_tracking_tables(
        engine
    )

    run_id = create_etl_run(
        engine=engine,
        source_clean_path=clean_file,
        target_schema=target_schema,
        target_table=target_table,
    )

    logger.info(
        "Début ETL run_id=%s | source=%s",
        run_id,
        clean_file,
    )

    try:
        frame, curated_path, transformation_stats = (
            transform_clean_file(
                clean_file
            )
        )

        duckdb_stats = verify_parquet_with_duckdb(
            curated_path
        )

        postgres_row_count = load_dataframe_to_postgres(
            frame=frame,
            engine=engine,
            target_schema=target_schema,
            target_table=target_table,
        )

        result: dict[str, Any] = {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "run_id": run_id,
            "status": "SUCCESS",
            "source_clean_path": str(
                clean_file
            ),
            "curated_path": str(
                curated_path
            ),
            "target_schema": target_schema,
            "target_table": target_table,
            **transformation_stats,
            **duckdb_stats,
            "postgres_row_count": postgres_row_count,
        }

        temporary_report_path = (
            ETL_REPORTS_DIR
            / "etl_report_latest.json"
        ).resolve()

        result["report_path"] = str(
            temporary_report_path
        )

        report_path = write_etl_report(
            result
        )

        result["report_path"] = str(
            report_path
        )

        mark_etl_run_success(
            engine=engine,
            run_id=run_id,
            result=result,
        )

        logger.info(
            "ETL réussi | run_id=%s | entrée=%s | sortie=%s | "
            "postgres=%s",
            run_id,
            result["input_rows"],
            result["output_rows"],
            result["postgres_row_count"],
        )

        return result

    except Exception as error:
        mark_etl_run_failed(
            engine=engine,
            run_id=run_id,
            error_message=str(error),
        )

        logger.exception(
            "Échec ETL run_id=%s : %s",
            run_id,
            error,
        )

        raise


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description=(
            "Transformer les données validées, créer le Parquet "
            "Curated et le charger dans PostgreSQL."
        )
    )

    parser.add_argument(
        "--clean",
        type=Path,
        default=None,
        help=(
            "Chemin d'un fichier *_validated.parquet. "
            "Par défaut, le fichier le plus récent est utilisé."
        ),
    )

    parser.add_argument(
        "--schema",
        default=DEFAULT_TARGET_SCHEMA,
        help="Schéma PostgreSQL cible.",
    )

    parser.add_argument(
        "--table",
        default=DEFAULT_TARGET_TABLE,
        help="Table PostgreSQL cible.",
    )

    return parser.parse_args()


def main() -> None:
    """Lancer le pipeline ETL."""
    arguments = parse_arguments()

    result = run_etl(
        clean_path=arguments.clean,
        target_schema=arguments.schema,
        target_table=arguments.table,
    )

    print()
    print("RESULTAT DU PIPELINE ETL")

    keys_to_display = (
        "run_id",
        "status",
        "source_clean_path",
        "curated_path",
        "input_rows",
        "output_rows",
        "duplicates_removed",
        "source_columns",
        "output_columns",
        "duckdb_row_count",
        "postgres_row_count",
        "target_schema",
        "target_table",
        "report_path",
    )

    for key in keys_to_display:
        print(f"{key}: {result[key]}")


if __name__ == "__main__":
    main()