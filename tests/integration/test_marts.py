"""
Tests d'integration pour le Data Warehouse et les Data Marts (Etapes 9-10).

Necessite une base PostgreSQL demarree (docker compose up -d) avec le
pipeline complet deja execute : ingestion, validation, ETL, Feature
Engineering, build_warehouse, build_marts.
"""

from sqlalchemy import text

from src.utils.database import get_engine
from src.warehouse.build_marts import MART_VIEWS


def test_all_mart_views_are_queryable() -> None:
    engine = get_engine()

    with engine.connect() as connection:
        for view_name in MART_VIEWS:
            row_count = connection.execute(
                text(f"SELECT COUNT(*) FROM marts.{view_name}")
            ).scalar_one()

            assert row_count >= 0


def test_mart_patients_matches_dim_patient_count() -> None:
    engine = get_engine()

    with engine.connect() as connection:
        dim_count = connection.execute(
            text("SELECT COUNT(*) FROM warehouse.dim_patient")
        ).scalar_one()

        mart_count = connection.execute(
            text("SELECT COUNT(*) FROM marts.mart_patients")
        ).scalar_one()

    assert dim_count == mart_count


def test_mart_hospitalizations_matches_fact_hospitalization_count() -> None:
    engine = get_engine()

    with engine.connect() as connection:
        fact_count = connection.execute(
            text("SELECT COUNT(*) FROM warehouse.fact_hospitalization")
        ).scalar_one()

        mart_count = connection.execute(
            text("SELECT COUNT(*) FROM marts.mart_hospitalizations")
        ).scalar_one()

    assert fact_count == mart_count


def test_mart_readmission_rate_is_between_zero_and_one() -> None:
    engine = get_engine()

    with engine.connect() as connection:
        rate = connection.execute(
            text("SELECT AVG(readmitted_30_days::float) FROM marts.mart_readmission")
        ).scalar_one()

    assert 0.0 <= rate <= 1.0


def test_mart_diagnostics_groups_are_known_categories() -> None:
    known_groups = {
        "Diabetes", "Circulatory", "Respiratory", "Digestive",
        "Injury", "Musculoskeletal", "Genitourinary", "Neoplasms", "Other",
    }

    engine = get_engine()

    with engine.connect() as connection:
        groups = {
            row[0]
            for row in connection.execute(
                text("SELECT DISTINCT diagnosis_group FROM marts.mart_diagnostics")
            )
        }

    assert groups.issubset(known_groups)
