import re
from pathlib import Path
from typing import Any

import polars as pl
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.utils.logging_config import get_logger
from src.utils.paths import WAREHOUSE_DIR

logger = get_logger("etl_loading")

DEFAULT_TARGET_SCHEMA = "staging"
DEFAULT_TARGET_TABLE = "hospital_encounters_curated"

IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)


def validate_identifier(
    identifier: str,
) -> None:
    """Protéger les noms de schéma, table et index."""
    if not IDENTIFIER_PATTERN.fullmatch(
        identifier
    ):
        raise ValueError(
            f"Identifiant SQL invalide : {identifier}"
        )


def execute_sql_script(
    engine: Engine,
    sql_path: Path,
) -> None:
    """Exécuter un fichier SQL contenant plusieurs instructions."""
    if not sql_path.exists():
        raise FileNotFoundError(
            f"Script SQL introuvable : {sql_path}"
        )

    sql_content = sql_path.read_text(
        encoding="utf-8-sig"
    )

    statements = [
        statement.strip()
        for statement in sql_content.split(";")
        if statement.strip()
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(
                statement
            )


def ensure_etl_tracking_tables(
    engine: Engine,
) -> None:
    """Créer le schéma staging et la table etl_runs."""
    ddl_path = (
        WAREHOUSE_DIR
        / "ddl"
        / "003_create_etl_tables.sql"
    )

    execute_sql_script(
        engine,
        ddl_path,
    )


def create_etl_run(
    engine: Engine,
    source_clean_path: Path,
    target_schema: str = DEFAULT_TARGET_SCHEMA,
    target_table: str = DEFAULT_TARGET_TABLE,
) -> int:
    """Créer une exécution ETL avec le statut RUNNING."""
    validate_identifier(target_schema)
    validate_identifier(target_table)

    query = text(
        """
        INSERT INTO etl_runs (
            source_clean_file_name,
            source_clean_path,
            target_schema,
            target_table,
            status
        )
        VALUES (
            :source_clean_file_name,
            :source_clean_path,
            :target_schema,
            :target_table,
            'RUNNING'
        )
        RETURNING id
        """
    )

    with engine.begin() as connection:
        run_id = connection.execute(
            query,
            {
                "source_clean_file_name": source_clean_path.name,
                "source_clean_path": str(
                    source_clean_path.resolve()
                ),
                "target_schema": target_schema,
                "target_table": target_table,
            },
        ).scalar_one()

    return int(run_id)


def create_curated_indexes(
    engine: Engine,
    target_schema: str,
    target_table: str,
) -> None:
    """Créer les index nécessaires sur la table Curated."""
    validate_identifier(target_schema)
    validate_identifier(target_table)

    encounter_index = (
        f"ux_{target_table}_encounter_id"
    )

    patient_index = (
        f"ix_{target_table}_patient_nbr"
    )

    readmitted_index = (
        f"ix_{target_table}_readmitted"
    )

    for index_name in (
        encounter_index,
        patient_index,
        readmitted_index,
    ):
        validate_identifier(index_name)

    statements = [
        f"""
        CREATE UNIQUE INDEX IF NOT EXISTS "{encounter_index}"
        ON "{target_schema}"."{target_table}" ("encounter_id")
        """,
        f"""
        CREATE INDEX IF NOT EXISTS "{patient_index}"
        ON "{target_schema}"."{target_table}" ("patient_nbr")
        """,
        f"""
        CREATE INDEX IF NOT EXISTS "{readmitted_index}"
        ON "{target_schema}"."{target_table}" ("readmitted")
        """,
        f"""
        ANALYZE "{target_schema}"."{target_table}"
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(
                statement
            )


def load_dataframe_to_postgres(
    frame: pl.DataFrame,
    engine: Engine,
    target_schema: str = DEFAULT_TARGET_SCHEMA,
    target_table: str = DEFAULT_TARGET_TABLE,
) -> int:
    """
    Charger le DataFrame Curated dans PostgreSQL.

    if_exists='replace' permet de conserver une table idempotente :
    une nouvelle exécution remplace la version précédente au lieu de
    dupliquer toutes les lignes.
    """
    validate_identifier(target_schema)
    validate_identifier(target_table)

    if frame.height == 0:
        raise ValueError(
            "Impossible de charger un DataFrame vide."
        )

    pandas_frame = frame.to_pandas()

    logger.info(
        "Chargement PostgreSQL | table=%s.%s | lignes=%s",
        target_schema,
        target_table,
        frame.height,
    )

    with engine.begin() as connection:
        pandas_frame.to_sql(
            name=target_table,
            con=connection,
            schema=target_schema,
            if_exists="replace",
            index=False,
            chunksize=500,
            method="multi",
        )

    create_curated_indexes(
        engine=engine,
        target_schema=target_schema,
        target_table=target_table,
    )

    postgres_row_count = get_postgres_row_count(
        engine=engine,
        target_schema=target_schema,
        target_table=target_table,
    )

    if postgres_row_count != frame.height:
        raise RuntimeError(
            "Le nombre de lignes PostgreSQL ne correspond pas "
            "au nombre de lignes du DataFrame."
        )

    logger.info(
        "Chargement PostgreSQL réussi | lignes=%s",
        postgres_row_count,
    )

    return postgres_row_count


def get_postgres_row_count(
    engine: Engine,
    target_schema: str = DEFAULT_TARGET_SCHEMA,
    target_table: str = DEFAULT_TARGET_TABLE,
) -> int:
    """Compter les lignes de la table PostgreSQL."""
    validate_identifier(target_schema)
    validate_identifier(target_table)

    query = text(
        f"""
        SELECT COUNT(*)
        FROM "{target_schema}"."{target_table}"
        """
    )

    with engine.connect() as connection:
        row_count = connection.execute(
            query
        ).scalar_one()

    return int(row_count)


def mark_etl_run_success(
    engine: Engine,
    run_id: int,
    result: dict[str, Any],
) -> None:
    """Enregistrer la réussite du pipeline ETL."""
    query = text(
        """
        UPDATE etl_runs
        SET status = 'SUCCESS',
            curated_path = :curated_path,
            input_rows = :input_rows,
            output_rows = :output_rows,
            duplicates_removed = :duplicates_removed,
            source_columns = :source_columns,
            output_columns = :output_columns,
            duckdb_row_count = :duckdb_row_count,
            postgres_row_count = :postgres_row_count,
            report_path = :report_path,
            finished_at = CURRENT_TIMESTAMP
        WHERE id = :run_id
        """
    )

    values = {
        "run_id": run_id,
        "curated_path": result["curated_path"],
        "input_rows": result["input_rows"],
        "output_rows": result["output_rows"],
        "duplicates_removed": result["duplicates_removed"],
        "source_columns": result["source_columns"],
        "output_columns": result["output_columns"],
        "duckdb_row_count": result["duckdb_row_count"],
        "postgres_row_count": result["postgres_row_count"],
        "report_path": result["report_path"],
    }

    with engine.begin() as connection:
        connection.execute(
            query,
            values,
        )


def mark_etl_run_failed(
    engine: Engine,
    run_id: int,
    error_message: str,
) -> None:
    """Enregistrer l'échec du pipeline ETL."""
    query = text(
        """
        UPDATE etl_runs
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