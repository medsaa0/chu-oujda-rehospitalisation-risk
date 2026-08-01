import polars as pl
import pytest

from src.validation.schema import EXPECTED_COLUMNS
from src.validation.validate_raw import (
    build_violations,
    validate_required_schema,
)


def create_valid_row(
    encounter_id: str = "1",
) -> dict[str, str]:
    """Créer une ligne valide pour les tests."""
    row = {
        column: "No"
        for column in EXPECTED_COLUMNS
    }

    row.update(
        {
            "encounter_id": encounter_id,
            "patient_nbr": "100",
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
            "diag_2": "401",
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


def test_schema_accepts_expected_columns() -> None:
    frame = pl.DataFrame(
        [create_valid_row()]
    )

    validate_required_schema(frame)


def test_schema_rejects_missing_column() -> None:
    row = create_valid_row()
    del row["readmitted"]

    frame = pl.DataFrame([row])

    with pytest.raises(
        ValueError,
        match="Colonnes obligatoires absentes",
    ):
        validate_required_schema(frame)


def test_valid_row_has_no_violation() -> None:
    frame = (
        pl.DataFrame([create_valid_row()])
        .with_row_index("__row_id")
    )

    violations = build_violations(frame)

    assert violations.height == 0


def test_invalid_values_are_detected() -> None:
    row = create_valid_row()
    row["time_in_hospital"] = "0"
    row["age"] = "invalid_age"
    row["readmitted"] = "UNKNOWN"

    frame = (
        pl.DataFrame([row])
        .with_row_index("__row_id")
    )

    violations = build_violations(frame)

    rules = set(
        violations.get_column(
            "rule_name"
        ).to_list()
    )

    assert "invalid_numeric_value" in rules
    assert "invalid_category" in rules


def test_duplicate_rows_are_detected() -> None:
    row = create_valid_row()

    frame = (
        pl.DataFrame([row, row])
        .with_row_index("__row_id")
    )

    violations = build_violations(frame)

    rules = set(
        violations.get_column(
            "rule_name"
        ).to_list()
    )

    assert "duplicate_encounter_id" in rules
    assert "exact_duplicate_row" in rules