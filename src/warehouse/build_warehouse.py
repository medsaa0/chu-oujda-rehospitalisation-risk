"""
Construction du Data Warehouse PostgreSQL en modele en etoile (Etape 9).

Cree les tables warehouse.dim_* et warehouse.fact_* (voir warehouse/ddl)
puis les peuple a partir de staging.hospital_encounters_curated et
staging.hospital_encounters_features (deja charges par les Etapes 7 et 8).
"""

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import polars as pl
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.features.build_features import MEDICATION_COLUMNS, diagnosis_group_expr
from src.loading.load_postgres import execute_sql_script, validate_identifier
from src.utils.database import get_engine
from src.utils.logging_config import get_logger
from src.utils.paths import SOURCE_DIR, WAREHOUSE_DIR

logger = get_logger("data_warehouse")

IDS_MAPPING_PATH = SOURCE_DIR / "IDS_mapping.csv"

CALENDAR_START_YEAR = 1999
CALENDAR_END_YEAR = 2008

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

DAY_NAMES = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday",
)


def ensure_warehouse_schema(engine: Engine) -> None:
    """Creer le schema warehouse, les dimensions et les tables de faits."""
    for ddl_file_name in (
        "004_create_warehouse_dimensions.sql",
        "005_create_warehouse_facts.sql",
    ):
        execute_sql_script(
            engine,
            WAREHOUSE_DIR / "ddl" / ddl_file_name,
        )


def parse_ids_mapping(csv_path: Path) -> dict[str, list[tuple[int, str]]]:
    """
    Lire IDS_mapping.csv (trois mini-tables empilees separees par une
    ligne vide) et retourner un dictionnaire section -> lignes (id, description).
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {csv_path}")

    sections: dict[str, list[tuple[int, str]]] = {
        "admission_type_id": [],
        "discharge_disposition_id": [],
        "admission_source_id": [],
    }

    current_section: str | None = None

    with csv_path.open(encoding="utf-8-sig", newline="") as file_handle:
        for row in csv.reader(file_handle):
            if not row or not row[0].strip():
                current_section = None
                continue

            identifier_column = row[0].strip()

            if identifier_column in sections:
                current_section = identifier_column
                continue

            if current_section is None:
                continue

            try:
                identifier_value = int(identifier_column)
            except ValueError:
                continue

            description = row[1].strip() if len(row) > 1 else ""
            sections[current_section].append(
                (identifier_value, description or "Non disponible")
            )

    return sections


def load_admission_reference_dimensions(engine: Engine) -> dict[str, int]:
    """Charger les trois dimensions issues de IDS_mapping.csv."""
    sections = parse_ids_mapping(IDS_MAPPING_PATH)

    table_by_section = {
        "admission_type_id": (
            "dim_admission_type",
            "admission_type_id",
            "admission_type_description",
        ),
        "discharge_disposition_id": (
            "dim_discharge_disposition",
            "discharge_disposition_id",
            "discharge_disposition_description",
        ),
        "admission_source_id": (
            "dim_admission_source",
            "admission_source_id",
            "admission_source_description",
        ),
    }

    row_counts: dict[str, int] = {}

    with engine.begin() as connection:
        for section_name, rows in sections.items():
            table_name, id_column, description_column = table_by_section[
                section_name
            ]

            connection.exec_driver_sql(
                f"TRUNCATE TABLE warehouse.{table_name} CASCADE"
            )

            connection.execute(
                text(
                    f"""
                    INSERT INTO warehouse.{table_name}
                        ({id_column}, {description_column})
                    VALUES (:identifier, :description)
                    """
                ),
                [
                    {"identifier": identifier, "description": description}
                    for identifier, description in rows
                ],
            )

            row_counts[table_name] = len(rows)

    logger.info(
        "Dimensions d'admission chargees | %s",
        row_counts,
    )

    return row_counts


def load_dim_patient(engine: Engine) -> int:
    """
    Peupler dim_patient a partir de la premiere hospitalisation connue
    de chaque patient (simplification Type 1, voir commentaire SQL).
    """
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE TABLE warehouse.dim_patient CASCADE"
        )

        connection.exec_driver_sql(
            """
            INSERT INTO warehouse.dim_patient
                (patient_nbr, gender, race, first_age_bracket, first_age_midpoint)
            SELECT DISTINCT ON (c.patient_nbr)
                c.patient_nbr,
                c.gender,
                c.race,
                c.age,
                f.age_midpoint
            FROM staging.hospital_encounters_curated c
            JOIN staging.hospital_encounters_features f
                ON f.encounter_id = c.encounter_id
            ORDER BY c.patient_nbr, c.encounter_id
            """
        )

        row_count = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM warehouse.dim_patient"
        ).scalar_one()

    logger.info("dim_patient charge | lignes=%s", row_count)

    return int(row_count)


def load_dim_diagnosis(engine: Engine) -> int:
    """Peupler dim_diagnosis a partir des codes distincts diag_1/2/3."""
    with engine.connect() as connection:
        codes_frame = pl.read_database(
            """
            SELECT diag_1 AS diagnosis_code FROM staging.hospital_encounters_curated
            WHERE diag_1 IS NOT NULL
            UNION
            SELECT diag_2 FROM staging.hospital_encounters_curated
            WHERE diag_2 IS NOT NULL
            UNION
            SELECT diag_3 FROM staging.hospital_encounters_curated
            WHERE diag_3 IS NOT NULL
            """,
            connection,
        )

    codes_frame = codes_frame.with_columns(
        diagnosis_group_expr("diagnosis_code")
    ).select(
        "diagnosis_code",
        pl.col("diagnosis_code_group").alias("diagnosis_group"),
    )

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE TABLE warehouse.dim_diagnosis CASCADE"
        )

        connection.execute(
            text(
                """
                INSERT INTO warehouse.dim_diagnosis
                    (diagnosis_code, diagnosis_group)
                VALUES (:diagnosis_code, :diagnosis_group)
                """
            ),
            codes_frame.to_dicts(),
        )

    logger.info("dim_diagnosis charge | lignes=%s", codes_frame.height)

    return codes_frame.height


def load_dim_medication(engine: Engine) -> int:
    """Peupler dim_medication avec la liste fixe des 23 medicaments."""
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE TABLE warehouse.dim_medication CASCADE"
        )

        connection.execute(
            text(
                """
                INSERT INTO warehouse.dim_medication (medication_name)
                VALUES (:medication_name)
                """
            ),
            [
                {"medication_name": column_name}
                for column_name in MEDICATION_COLUMNS
            ],
        )

    logger.info(
        "dim_medication charge | lignes=%s",
        len(MEDICATION_COLUMNS),
    )

    return len(MEDICATION_COLUMNS)


def generate_calendar_rows() -> list[dict[str, Any]]:
    """Generer les lignes de dim_date pour 1999-2008."""
    start = date(CALENDAR_START_YEAR, 1, 1)
    end = date(CALENDAR_END_YEAR, 12, 31)

    rows: list[dict[str, Any]] = []
    current = start

    while current <= end:
        rows.append(
            {
                "date_key": int(current.strftime("%Y%m%d")),
                "full_date": current,
                "day_of_month": current.day,
                "month_number": current.month,
                "month_name": MONTH_NAMES[current.month - 1],
                "quarter_number": (current.month - 1) // 3 + 1,
                "year_number": current.year,
                "day_of_week_number": current.isoweekday(),
                "day_name": DAY_NAMES[current.isoweekday() - 1],
                "is_weekend": current.isoweekday() in (6, 7),
            }
        )

        current += timedelta(days=1)

    return rows


def load_dim_date(engine: Engine) -> int:
    """Peupler la table calendrier technique (non reliee aux faits)."""
    rows = generate_calendar_rows()

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO warehouse.dim_date (
                    date_key, full_date, day_of_month, month_number,
                    month_name, quarter_number, year_number,
                    day_of_week_number, day_name, is_weekend
                )
                VALUES (
                    :date_key, :full_date, :day_of_month, :month_number,
                    :month_name, :quarter_number, :year_number,
                    :day_of_week_number, :day_name, :is_weekend
                )
                ON CONFLICT (date_key) DO NOTHING
                """
            ),
            rows,
        )

    logger.info("dim_date charge | lignes=%s", len(rows))

    return len(rows)


def load_fact_hospitalization(engine: Engine) -> int:
    """Peupler fact_hospitalization par jointure staging + dimensions."""
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE TABLE warehouse.fact_medication_usage CASCADE"
        )
        connection.exec_driver_sql(
            "TRUNCATE TABLE warehouse.fact_readmission CASCADE"
        )
        connection.exec_driver_sql(
            "TRUNCATE TABLE warehouse.fact_hospitalization CASCADE"
        )

        connection.exec_driver_sql(
            """
            INSERT INTO warehouse.fact_hospitalization (
                encounter_key, patient_key, admission_type_id,
                discharge_disposition_id, admission_source_id,
                diag_1_key, diag_2_key, diag_3_key,
                time_in_hospital, num_lab_procedures, num_procedures,
                num_medications, number_diagnoses, total_previous_visits,
                healthcare_utilization_score, patient_complexity_score
            )
            SELECT
                c.encounter_id,
                p.patient_key,
                c.admission_type_id,
                c.discharge_disposition_id,
                c.admission_source_id,
                d1.diagnosis_key,
                d2.diagnosis_key,
                d3.diagnosis_key,
                c.time_in_hospital,
                c.num_lab_procedures,
                c.num_procedures,
                c.num_medications,
                c.number_diagnoses,
                f.total_previous_visits,
                f.healthcare_utilization_score,
                f.patient_complexity_score
            FROM staging.hospital_encounters_curated c
            JOIN staging.hospital_encounters_features f
                ON f.encounter_id = c.encounter_id
            JOIN warehouse.dim_patient p
                ON p.patient_nbr = c.patient_nbr
            LEFT JOIN warehouse.dim_diagnosis d1
                ON d1.diagnosis_code = c.diag_1
            LEFT JOIN warehouse.dim_diagnosis d2
                ON d2.diagnosis_code = c.diag_2
            LEFT JOIN warehouse.dim_diagnosis d3
                ON d3.diagnosis_code = c.diag_3
            """
        )

        row_count = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM warehouse.fact_hospitalization"
        ).scalar_one()

    logger.info("fact_hospitalization charge | lignes=%s", row_count)

    return int(row_count)


def load_fact_readmission(engine: Engine) -> int:
    """Peupler fact_readmission a partir des Features."""
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            INSERT INTO warehouse.fact_readmission (
                encounter_key, readmitted, readmitted_30_days,
                readmitted_flag, is_frequent_patient, insulin_prescribed,
                high_medication_burden_flag
            )
            SELECT
                c.encounter_id,
                c.readmitted,
                f.readmitted_30_days,
                f.readmitted_flag,
                f.is_frequent_patient,
                f.insulin_prescribed,
                f.high_medication_burden_flag
            FROM staging.hospital_encounters_curated c
            JOIN staging.hospital_encounters_features f
                ON f.encounter_id = c.encounter_id
            """
        )

        row_count = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM warehouse.fact_readmission"
        ).scalar_one()

    logger.info("fact_readmission charge | lignes=%s", row_count)

    return int(row_count)


def load_fact_medication_usage(engine: Engine) -> int:
    """
    Peupler fact_medication_usage (bridge encounter x medicament).

    Seuls les medicaments effectivement prescrits (status != 'No')
    sont conserves.
    """
    for column_name in MEDICATION_COLUMNS:
        validate_identifier(column_name)

    union_select = " UNION ALL ".join(
        f"""
        SELECT
            c.encounter_id AS encounter_key,
            '{column_name}' AS medication_name,
            c.{column_name} AS status
        FROM staging.hospital_encounters_curated c
        WHERE c.{column_name} != 'No'
        """
        for column_name in MEDICATION_COLUMNS
    )

    with engine.begin() as connection:
        connection.exec_driver_sql(
            f"""
            INSERT INTO warehouse.fact_medication_usage (
                encounter_key, medication_key, status, dosage_changed
            )
            SELECT
                usage.encounter_key,
                m.medication_key,
                usage.status,
                CASE WHEN usage.status IN ('Up', 'Down') THEN 1 ELSE 0 END
            FROM ({union_select}) AS usage
            JOIN warehouse.dim_medication m
                ON m.medication_name = usage.medication_name
            """
        )

        row_count = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM warehouse.fact_medication_usage"
        ).scalar_one()

    logger.info("fact_medication_usage charge | lignes=%s", row_count)

    return int(row_count)


def build_warehouse() -> dict[str, Any]:
    """Executer l'ensemble de la construction du Data Warehouse."""
    engine = get_engine()

    logger.info("Debut de la construction du Data Warehouse")

    ensure_warehouse_schema(engine)

    admission_rows = load_admission_reference_dimensions(engine)
    patient_rows = load_dim_patient(engine)
    diagnosis_rows = load_dim_diagnosis(engine)
    medication_rows = load_dim_medication(engine)
    date_rows = load_dim_date(engine)

    hospitalization_rows = load_fact_hospitalization(engine)
    readmission_rows = load_fact_readmission(engine)
    medication_usage_rows = load_fact_medication_usage(engine)

    result = {
        "status": "SUCCESS",
        "dim_admission_type_rows": admission_rows["dim_admission_type"],
        "dim_discharge_disposition_rows": admission_rows[
            "dim_discharge_disposition"
        ],
        "dim_admission_source_rows": admission_rows["dim_admission_source"],
        "dim_patient_rows": patient_rows,
        "dim_diagnosis_rows": diagnosis_rows,
        "dim_medication_rows": medication_rows,
        "dim_date_rows": date_rows,
        "fact_hospitalization_rows": hospitalization_rows,
        "fact_readmission_rows": readmission_rows,
        "fact_medication_usage_rows": medication_usage_rows,
    }

    logger.info("Data Warehouse construit avec succes | %s", result)

    return result


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments de la ligne de commande."""
    return argparse.ArgumentParser(
        description=(
            "Construire le schema warehouse (dimensions + faits) a "
            "partir des tables staging."
        )
    ).parse_args()


def main() -> None:
    """Lancer la construction du Data Warehouse."""
    parse_arguments()

    result = build_warehouse()

    print()
    print("RESULTAT DE LA CONSTRUCTION DU DATA WAREHOUSE")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
