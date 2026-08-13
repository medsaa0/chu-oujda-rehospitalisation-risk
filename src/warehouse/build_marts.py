"""
Construction des Data Marts PostgreSQL (Etape 10).

Cree les vues du schema marts (warehouse/ddl/006_create_marts_views.sql),
au-dessus du Data Warehouse construit par build_warehouse.py, et
verifie qu'elles sont interrogeables.
"""

import argparse
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.loading.load_postgres import execute_sql_script
from src.utils.database import get_engine
from src.utils.logging_config import get_logger
from src.utils.paths import WAREHOUSE_DIR

logger = get_logger("data_marts")

MART_VIEWS = (
    "mart_patients",
    "mart_hospitalizations",
    "mart_readmission",
    "mart_diagnostics",
    "mart_medications",
    "mart_quality",
    "mart_quality_violations",
)


def ensure_marts_schema(engine: Engine) -> None:
    """Creer le schema marts et ses vues."""
    execute_sql_script(
        engine,
        WAREHOUSE_DIR / "ddl" / "006_create_marts_views.sql",
    )


def count_mart_rows(engine: Engine) -> dict[str, int]:
    """Compter les lignes de chaque vue mart pour verification."""
    row_counts: dict[str, int] = {}

    with engine.connect() as connection:
        for view_name in MART_VIEWS:
            row_count = connection.execute(
                text(f"SELECT COUNT(*) FROM marts.{view_name}")
            ).scalar_one()

            row_counts[view_name] = int(row_count)

    return row_counts


def build_marts() -> dict[str, Any]:
    """Creer les Data Marts et retourner leurs volumes."""
    engine = get_engine()

    logger.info("Debut de la construction des Data Marts")

    ensure_marts_schema(engine)

    row_counts = count_mart_rows(engine)

    logger.info("Data Marts construits avec succes | %s", row_counts)

    return {"status": "SUCCESS", **row_counts}


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments de la ligne de commande."""
    return argparse.ArgumentParser(
        description="Creer les vues des Data Marts PostgreSQL."
    ).parse_args()


def main() -> None:
    """Lancer la construction des Data Marts."""
    parse_arguments()

    result = build_marts()

    print()
    print("RESULTAT DE LA CONSTRUCTION DES DATA MARTS")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
