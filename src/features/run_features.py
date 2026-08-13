"""
Orchestration du Feature Engineering (Etape 8).

Calcule les features a partir du Parquet Curated, les charge dans
PostgreSQL (staging.hospital_encounters_features) et ecrit un rapport
JSON, sur le meme modele que src/transformation/run_etl.py.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.features.build_features import (
    build_features_from_file,
    resolve_curated_file,
)
from src.loading.load_postgres import load_dataframe_to_postgres
from src.utils.database import get_engine
from src.utils.logging_config import get_logger
from src.utils.paths import ROOT_DIR, create_required_directories

logger = get_logger("feature_pipeline")

DEFAULT_TARGET_SCHEMA = "staging"
DEFAULT_TARGET_TABLE = "hospital_encounters_features"

FEATURES_REPORTS_DIR = ROOT_DIR / "reports" / "features"


def write_features_report(result: dict[str, Any]) -> Path:
    """Créer le rapport JSON de la dernière exécution du Feature Engineering."""
    FEATURES_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report_path = FEATURES_REPORTS_DIR / "features_report_latest.json"

    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return report_path.resolve()


def run_features(
    curated_path: Path | None = None,
    target_schema: str = DEFAULT_TARGET_SCHEMA,
    target_table: str = DEFAULT_TARGET_TABLE,
) -> dict[str, Any]:
    """Calculer les Features, les charger dans PostgreSQL et faire le rapport."""
    create_required_directories()

    curated_file = resolve_curated_file(curated_path)

    logger.info(
        "Début Feature Engineering | source=%s",
        curated_file,
    )

    frame, features_path, statistics = build_features_from_file(
        curated_file
    )

    postgres_row_count = load_dataframe_to_postgres(
        frame=frame,
        engine=get_engine(),
        target_schema=target_schema,
        target_table=target_table,
        extra_index_columns=("readmitted_30_days",),
    )

    result: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "target_schema": target_schema,
        "target_table": target_table,
        **statistics,
        "postgres_row_count": postgres_row_count,
    }

    report_path = write_features_report(result)
    result["report_path"] = str(report_path)

    logger.info(
        "Feature Engineering réussi | lignes=%s | postgres=%s",
        result["output_rows"],
        postgres_row_count,
    )

    return result


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description=(
            "Calculer les Features et les charger dans PostgreSQL."
        )
    )

    parser.add_argument(
        "--curated",
        type=Path,
        default=None,
        help=(
            "Chemin d'un fichier *_curated.parquet. Par défaut, le "
            "fichier le plus récent est utilisé."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Lancer le pipeline Feature Engineering."""
    arguments = parse_arguments()

    result = run_features(curated_path=arguments.curated)

    print()
    print("RESULTAT DU FEATURE ENGINEERING")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
