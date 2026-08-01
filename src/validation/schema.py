from typing import Final

import pandera.polars as pa

EXPECTED_COLUMNS: Final[tuple[str, ...]] = (
    "encounter_id",
    "patient_nbr",
    "race",
    "gender",
    "age",
    "weight",
    "admission_type_id",
    "discharge_disposition_id",
    "admission_source_id",
    "time_in_hospital",
    "payer_code",
    "medical_specialty",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "diag_1",
    "diag_2",
    "diag_3",
    "number_diagnoses",
    "max_glu_serum",
    "A1Cresult",
    "metformin",
    "repaglinide",
    "nateglinide",
    "chlorpropamide",
    "glimepiride",
    "acetohexamide",
    "glipizide",
    "glyburide",
    "tolbutamide",
    "pioglitazone",
    "rosiglitazone",
    "acarbose",
    "miglitol",
    "troglitazone",
    "tolazamide",
    "examide",
    "citoglipton",
    "insulin",
    "glyburide-metformin",
    "glipizide-metformin",
    "glimepiride-pioglitazone",
    "metformin-rosiglitazone",
    "metformin-pioglitazone",
    "change",
    "diabetesMed",
    "readmitted",
)


AGE_VALUES: Final[set[str]] = {
    "[0-10)",
    "[10-20)",
    "[20-30)",
    "[30-40)",
    "[40-50)",
    "[50-60)",
    "[60-70)",
    "[70-80)",
    "[80-90)",
    "[90-100)",
}


MEDICATION_COLUMNS: Final[tuple[str, ...]] = (
    "metformin",
    "repaglinide",
    "nateglinide",
    "chlorpropamide",
    "glimepiride",
    "acetohexamide",
    "glipizide",
    "glyburide",
    "tolbutamide",
    "pioglitazone",
    "rosiglitazone",
    "acarbose",
    "miglitol",
    "troglitazone",
    "tolazamide",
    "examide",
    "citoglipton",
    "insulin",
    "glyburide-metformin",
    "glipizide-metformin",
    "glimepiride-pioglitazone",
    "metformin-rosiglitazone",
    "metformin-pioglitazone",
)


NUMERIC_RULES: Final[dict[str, tuple[int, int | None, str]]] = {
    "encounter_id": (
        1,
        None,
        "L'identifiant du séjour doit être un entier positif.",
    ),
    "patient_nbr": (
        1,
        None,
        "L'identifiant du patient doit être un entier positif.",
    ),
    "admission_type_id": (
        1,
        None,
        "Le type d'admission doit être un identifiant positif.",
    ),
    "discharge_disposition_id": (
        1,
        None,
        "Le mode de sortie doit être un identifiant positif.",
    ),
    "admission_source_id": (
        1,
        None,
        "La source d'admission doit être un identifiant positif.",
    ),
    "time_in_hospital": (
        1,
        14,
        "La durée du séjour doit être comprise entre 1 et 14 jours.",
    ),
    "num_lab_procedures": (
        0,
        None,
        "Le nombre d'analyses ne peut pas être négatif.",
    ),
    "num_procedures": (
        0,
        None,
        "Le nombre de procédures ne peut pas être négatif.",
    ),
    "num_medications": (
        0,
        None,
        "Le nombre de médicaments ne peut pas être négatif.",
    ),
    "number_outpatient": (
        0,
        None,
        "Le nombre de visites externes ne peut pas être négatif.",
    ),
    "number_emergency": (
        0,
        None,
        "Le nombre de visites aux urgences ne peut pas être négatif.",
    ),
    "number_inpatient": (
        0,
        None,
        "Le nombre d'hospitalisations précédentes ne peut pas être négatif.",
    ),
    "number_diagnoses": (
        1,
        16,
        "Le nombre de diagnostics doit être compris entre 1 et 16.",
    ),
}


CATEGORY_RULES: Final[dict[str, set[str]]] = {
    "race": {
        "Caucasian",
        "AfricanAmerican",
        "Asian",
        "Hispanic",
        "Other",
    },
    "gender": {
        "Female",
        "Male",
    },
    "age": AGE_VALUES,
    "max_glu_serum": {
        "None",
        "Norm",
        ">200",
        ">300",
    },
    "A1Cresult": {
        "None",
        "Norm",
        ">7",
        ">8",
    },
    "change": {
        "Ch",
        "No",
    },
    "diabetesMed": {
        "Yes",
        "No",
    },
    "readmitted": {
        "<30",
        ">30",
        "NO",
    },
}


for medication_column in MEDICATION_COLUMNS:
    CATEGORY_RULES[medication_column] = {
        "No",
        "Steady",
        "Up",
        "Down",
    }


CRITICAL_COLUMNS: Final[tuple[str, ...]] = (
    *NUMERIC_RULES.keys(),
    *(
        column
        for column in CATEGORY_RULES
        if column != "race"
    ),
)


RAW_DATA_SCHEMA = pa.DataFrameSchema(
    {
        column: pa.Column(
            required=True,
            nullable=True,
        )
        for column in EXPECTED_COLUMNS
    },
    strict=False,
    name="raw_hospital_data",
)