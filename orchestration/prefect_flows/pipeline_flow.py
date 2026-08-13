"""
Orchestration Prefect du pipeline complet (Etape 11).

Enchaine : Ingestion -> Validation -> ETL (nettoyage/transformation/
Parquet/PostgreSQL) -> Feature Engineering -> Data Warehouse -> Data
Marts, en reutilisant directement les fonctions Python des Etapes 5 a 10
(aucune duplication de logique).

Lancer une execution unique :
    python -m orchestration.prefect_flows.pipeline_flow

Deployer avec une planification (ex. tous les jours a 3h) :
    python -m orchestration.prefect_flows.pipeline_flow --serve --cron "0 3 * * *"
"""

import argparse
from typing import Any

from prefect import flow, get_run_logger, task
from prefect.states import State

from src.features.run_features import run_features
from src.ingestion.ingest_csv import EXPECTED_FILENAME, ingest_csv
from src.transformation.run_etl import run_etl
from src.utils.paths import SOURCE_DIR
from src.validation.validate_raw import validate_raw_data
from src.warehouse.build_marts import build_marts
from src.warehouse.build_warehouse import build_warehouse

TASK_RETRIES = 2
TASK_RETRY_DELAY_SECONDS = 30


@task(
    name="ingestion",
    retries=TASK_RETRIES,
    retry_delay_seconds=TASK_RETRY_DELAY_SECONDS,
)
def ingestion_task() -> dict[str, Any]:
    """Etape 5 : ingerer le CSV source dans la Landing/Raw Zone."""
    return ingest_csv(SOURCE_DIR / EXPECTED_FILENAME)


@task(
    name="validation",
    retries=TASK_RETRIES,
    retry_delay_seconds=TASK_RETRY_DELAY_SECONDS,
)
def validation_task(depends_on: dict[str, Any]) -> dict[str, Any]:
    """Etape 6 : controler la qualite du fichier Raw le plus recent."""
    return validate_raw_data()


@task(
    name="etl",
    retries=TASK_RETRIES,
    retry_delay_seconds=TASK_RETRY_DELAY_SECONDS,
)
def etl_task(depends_on: dict[str, Any]) -> dict[str, Any]:
    """Etape 7 : nettoyer, transformer et charger dans PostgreSQL."""
    return run_etl()


@task(
    name="feature_engineering",
    retries=TASK_RETRIES,
    retry_delay_seconds=TASK_RETRY_DELAY_SECONDS,
)
def features_task(depends_on: dict[str, Any]) -> dict[str, Any]:
    """Etape 8 : calculer les variables derivees."""
    return run_features()


@task(
    name="data_warehouse",
    retries=TASK_RETRIES,
    retry_delay_seconds=TASK_RETRY_DELAY_SECONDS,
)
def warehouse_task(depends_on: dict[str, Any]) -> dict[str, Any]:
    """Etape 9 : reconstruire le Data Warehouse en etoile."""
    return build_warehouse()


@task(
    name="data_marts",
    retries=TASK_RETRIES,
    retry_delay_seconds=TASK_RETRY_DELAY_SECONDS,
)
def marts_task(depends_on: dict[str, Any]) -> dict[str, Any]:
    """Etape 10 : (re)creer les vues des Data Marts."""
    return build_marts()


def notify_on_failure(flow_instance: Any, flow_run: Any, state: State) -> None:
    """
    Notifier l'echec du pipeline.

    Journalise une erreur claire. Un vrai canal de notification (email,
    Slack, Teams...) peut etre branche ici en production ; cela
    necessite des identifiants externes hors du perimetre de ce projet
    pedagogique.
    """
    print(
        f"[ALERTE PIPELINE] Execution {flow_run.name} en echec "
        f"(state={state.type})."
    )


@flow(
    name="hospital-readmission-pipeline",
    on_failure=[notify_on_failure],
)
def hospital_readmission_pipeline() -> dict[str, Any]:
    """
    Executer la chaine complete Data Engineering (Etapes 5 a 10).

    Chaque etape recoit le resultat de la precedente uniquement pour
    forcer l'ordre d'execution (wait_for implicite) ; en cas d'echec,
    Prefect interrompt le flow et retente chaque tache jusqu'a
    TASK_RETRIES fois avant d'abandonner.
    """
    logger = get_run_logger()

    logger.info("Debut du pipeline hospital-readmission-pipeline")

    ingestion_result = ingestion_task()
    validation_result = validation_task(depends_on=ingestion_result)
    etl_result = etl_task(depends_on=validation_result)
    features_result = features_task(depends_on=etl_result)
    warehouse_result = warehouse_task(depends_on=features_result)
    marts_result = marts_task(depends_on=warehouse_result)

    summary = {
        "ingestion": ingestion_result["status"],
        "validation": validation_result["status"],
        "etl": etl_result["status"],
        "feature_engineering": features_result["status"],
        "data_warehouse": warehouse_result["status"],
        "data_marts": marts_result["status"],
    }

    logger.info("Pipeline termine | %s", summary)

    return summary


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description=(
            "Executer ou deployer le pipeline Prefect complet "
            "(Ingestion -> Validation -> ETL -> Features -> "
            "Data Warehouse -> Data Marts)."
        )
    )

    parser.add_argument(
        "--serve",
        action="store_true",
        help=(
            "Deployer le flow avec une planification au lieu de "
            "l'executer une seule fois (bloquant, sert le flow en continu)."
        ),
    )

    parser.add_argument(
        "--cron",
        default="0 3 * * *",
        help="Expression cron utilisee avec --serve (defaut : 3h chaque jour).",
    )

    return parser.parse_args()


def main() -> None:
    """Lancer le pipeline en execution unique ou le deployer planifie."""
    arguments = parse_arguments()

    if arguments.serve:
        hospital_readmission_pipeline.serve(
            name="hospital-readmission-daily",
            cron=arguments.cron,
        )
        return

    result = hospital_readmission_pipeline()

    print()
    print("RESULTAT DU PIPELINE PREFECT")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
