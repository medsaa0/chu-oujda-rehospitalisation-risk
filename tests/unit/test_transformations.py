import polars as pl

from src.transformation.transform_clean import (
    transform_dataframe,
)
from src.validation.schema import EXPECTED_COLUMNS


def create_valid_row(
    encounter_id: str = "1",
    patient_nbr: str = "100",
) -> dict[str, str]:
    """Créer une ligne valide représentant le dataset hospitalier."""
    row = {
        column: "No"
        for column in EXPECTED_COLUMNS
    }

    row.update(
        {
            "encounter_id": encounter_id,
            "patient_nbr": patient_nbr,
            "race": "Caucasian",
            "gender": "Female",
            "age": "[50-60)",
            "weight": "?",
            "admission_type_id": "1",
            "discharge_disposition_id": "1",
            "admission_source_id": "1",
            "time_in_hospital": "4",
            "payer_code": "?",
            "medical_specialty": "?",
            "num_lab_procedures": "40",
            "num_procedures": "1",
            "num_medications": "12",
            "number_outpatient": "0",
            "number_emergency": "0",
            "number_inpatient": "0",
            "diag_1": "250.00",
            "diag_2": "v45",
            "diag_3": "428",
            "number_diagnoses": "5",
            "max_glu_serum": "None",
            "A1Cresult": "None",
            "change": "No",
            "diabetesMed": "Yes",
            "readmitted": "NO",
        }
    )

    return row


def test_numeric_columns_are_converted() -> None:
    frame = pl.DataFrame(
        [create_valid_row()]
    )

    transformed, _ = transform_dataframe(
        frame,
        source_file_name="test_validated.parquet",
    )

    assert transformed.schema[
        "encounter_id"
    ] == pl.Int64

    assert transformed.schema[
        "time_in_hospital"
    ] == pl.Int64

    assert transformed.schema[
        "num_medications"
    ] == pl.Int64


def test_question_marks_are_replaced() -> None:
    frame = pl.DataFrame(
        [create_valid_row()]
    )

    transformed, _ = transform_dataframe(
        frame,
        source_file_name="test_validated.parquet",
    )

    row = transformed.row(
        0,
        named=True,
    )

    assert row["weight"] == "Unknown"
    assert row["payer_code"] == "Unknown"
    assert row["medical_specialty"] == "Unknown"


def test_diagnosis_codes_are_normalized() -> None:
    frame = pl.DataFrame(
        [create_valid_row()]
    )

    transformed, _ = transform_dataframe(
        frame,
        source_file_name="test_validated.parquet",
    )

    assert transformed.get_column(
        "diag_2"
    )[0] == "V45"


def test_column_names_are_postgresql_friendly() -> None:
    frame = pl.DataFrame(
        [create_valid_row()]
    )

    transformed, _ = transform_dataframe(
        frame,
        source_file_name="test_validated.parquet",
    )

    assert "A1Cresult" not in transformed.columns
    assert "a1c_result" in transformed.columns

    assert "glyburide-metformin" not in transformed.columns
    assert "glyburide_metformin" in transformed.columns


def test_duplicate_encounters_are_removed() -> None:
    first_row = create_valid_row(
        encounter_id="1",
    )

    second_row = create_valid_row(
        encounter_id="1",
    )

    second_row["patient_nbr"] = "200"

    frame = pl.DataFrame(
        [
            first_row,
            second_row,
        ]
    )

    transformed, statistics = transform_dataframe(
        frame,
        source_file_name="test_validated.parquet",
    )

    assert transformed.height == 1
    assert statistics["duplicates_removed"] == 1


def test_etl_metadata_is_added() -> None:
    frame = pl.DataFrame(
        [create_valid_row()]
    )

    transformed, _ = transform_dataframe(
        frame,
        source_file_name="test_validated.parquet",
    )

    assert "etl_processed_at" in transformed.columns
    assert "etl_source_file" in transformed.columns
    assert "etl_version" in transformed.columns

    assert transformed.get_column(
        "etl_source_file"
    )[0] == "test_validated.parquet"