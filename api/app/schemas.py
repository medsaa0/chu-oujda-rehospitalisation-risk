"""Schemas Pydantic de l'API (requetes et reponses)."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database: str


class KPIResponse(BaseModel):
    total_hospitalizations: int
    total_patients: int
    total_readmissions: int
    readmission_rate: float
    readmitted_30_days_rate: float
    avg_time_in_hospital: float
    avg_num_medications: float
    avg_number_diagnoses: float


class DataQualityRunResponse(BaseModel):
    quality_run_id: int
    raw_file_name: str
    status: str
    total_rows: int | None
    valid_rows: int | None
    rejected_rows: int | None
    total_violations: int | None
    duplicate_rows: int | None
    valid_rate_percent: float | None
    started_at: str | None
    finished_at: str | None


class PipelineRunResponse(BaseModel):
    run_id: int
    status: str
    target_schema: str
    target_table: str
    input_rows: int | None
    output_rows: int | None
    started_at: str | None
    finished_at: str | None
    error_message: str | None


class PredictionRequest(BaseModel):
    """Variables attendues par le modele (voir ml/training/train_models.py)."""

    time_in_hospital: int = Field(ge=1, le=14)
    num_lab_procedures: int = Field(ge=0)
    num_procedures: int = Field(ge=0)
    num_medications: int = Field(ge=0)
    number_diagnoses: int = Field(ge=1, le=16)
    age_midpoint: int = Field(ge=0, le=100)
    total_previous_visits: int = Field(ge=0)
    healthcare_utilization_score: int = Field(ge=0)
    patient_complexity_score: int = Field(ge=0)
    active_medications_count: int = Field(ge=0)
    medication_dosage_changes_count: int = Field(ge=0)
    gender: str
    race: str
    admission_type_id: int
    discharge_disposition_id: int
    admission_source_id: int
    max_glu_serum: str
    a1c_result: str
    change: str
    diabetesmed: str
    insulin_prescribed: int = Field(ge=0, le=1)
    diag_1_group: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "time_in_hospital": 4,
                "num_lab_procedures": 40,
                "num_procedures": 1,
                "num_medications": 12,
                "number_diagnoses": 5,
                "age_midpoint": 55,
                "total_previous_visits": 1,
                "healthcare_utilization_score": 5,
                "patient_complexity_score": 22,
                "active_medications_count": 2,
                "medication_dosage_changes_count": 0,
                "gender": "Female",
                "race": "Caucasian",
                "admission_type_id": 1,
                "discharge_disposition_id": 1,
                "admission_source_id": 7,
                "max_glu_serum": "None",
                "a1c_result": "None",
                "change": "No",
                "diabetesmed": "Yes",
                "insulin_prescribed": 1,
                "diag_1_group": "Diabetes",
            }
        }
    }


class PredictionResponse(BaseModel):
    predicted_probability: float
    predicted_risk_category: str
    model_name: str
