import polars as pl

from src.features.build_features import build_feature_frame


def create_curated_row(**overrides: object) -> dict[str, object]:
    """Créer une ligne minimale représentant le Parquet Curated."""
    row: dict[str, object] = {
        "encounter_id": 1,
        "patient_nbr": 100,
        "race": "Caucasian",
        "gender": "Female",
        "age": "[50-60)",
        "weight": "Unknown",
        "admission_type_id": 1,
        "discharge_disposition_id": 1,
        "admission_source_id": 1,
        "time_in_hospital": 4,
        "payer_code": "Unknown",
        "medical_specialty": "Unknown",
        "num_lab_procedures": 40,
        "num_procedures": 1,
        "num_medications": 12,
        "number_outpatient": 1,
        "number_emergency": 0,
        "number_inpatient": 2,
        "diag_1": "250.83",
        "diag_2": "V45",
        "diag_3": "428",
        "number_diagnoses": 5,
        "max_glu_serum": "None",
        "a1c_result": "None",
        "metformin": "No",
        "repaglinide": "No",
        "nateglinide": "No",
        "chlorpropamide": "No",
        "glimepiride": "No",
        "acetohexamide": "No",
        "glipizide": "No",
        "glyburide": "No",
        "tolbutamide": "No",
        "pioglitazone": "No",
        "rosiglitazone": "No",
        "acarbose": "No",
        "miglitol": "No",
        "troglitazone": "No",
        "tolazamide": "No",
        "examide": "No",
        "citoglipton": "No",
        "insulin": "Up",
        "glyburide_metformin": "No",
        "glipizide_metformin": "No",
        "glimepiride_pioglitazone": "No",
        "metformin_rosiglitazone": "No",
        "metformin_pioglitazone": "No",
        "change": "Ch",
        "diabetesmed": "Yes",
        "readmitted": "<30",
    }

    row.update(overrides)

    return row


def test_readmitted_30_days_flag() -> None:
    frame = pl.DataFrame([create_curated_row()])

    features, _ = build_feature_frame(frame)

    assert features.get_column("readmitted_30_days")[0] == 1
    assert features.get_column("readmitted_flag")[0] == 1


def test_readmitted_no_gives_zero_flags() -> None:
    frame = pl.DataFrame(
        [create_curated_row(encounter_id=2, readmitted="NO")]
    )

    features, _ = build_feature_frame(frame)

    assert features.get_column("readmitted_30_days")[0] == 0
    assert features.get_column("readmitted_flag")[0] == 0


def test_total_previous_visits_sums_three_columns() -> None:
    frame = pl.DataFrame([create_curated_row()])

    features, _ = build_feature_frame(frame)

    assert features.get_column("total_previous_visits")[0] == 3


def test_diagnosis_group_diabetes() -> None:
    frame = pl.DataFrame([create_curated_row()])

    features, _ = build_feature_frame(frame)

    assert features.get_column("diag_1_group")[0] == "Diabetes"


def test_diagnosis_group_circulatory() -> None:
    frame = pl.DataFrame(
        [create_curated_row(encounter_id=3, diag_1="428.0")]
    )

    features, _ = build_feature_frame(frame)

    assert features.get_column("diag_1_group")[0] == "Circulatory"


def test_diagnosis_group_other_for_v_codes() -> None:
    frame = pl.DataFrame([create_curated_row()])

    features, _ = build_feature_frame(frame)

    assert features.get_column("diag_2_group")[0] == "Other"


def test_insulin_prescribed_flag() -> None:
    frame = pl.DataFrame([create_curated_row()])

    features, _ = build_feature_frame(frame)

    assert features.get_column("insulin_prescribed")[0] == 1


def test_age_midpoint_lookup() -> None:
    frame = pl.DataFrame([create_curated_row()])

    features, _ = build_feature_frame(frame)

    assert features.get_column("age_midpoint")[0] == 55


def test_encounter_id_is_unique() -> None:
    frame = pl.DataFrame(
        [
            create_curated_row(encounter_id=1),
            create_curated_row(encounter_id=2, readmitted="NO"),
        ]
    )

    features, statistics = build_feature_frame(frame)

    assert features.get_column("encounter_id").n_unique() == 2
    assert statistics["output_rows"] == 2
