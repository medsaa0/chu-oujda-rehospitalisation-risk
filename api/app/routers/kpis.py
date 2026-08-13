"""GET /api/kpis : indicateurs globaux (voir docs/business/kpis.md)."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from api.app.dependencies import get_db_engine
from api.app.schemas import KPIResponse

router = APIRouter(prefix="/api", tags=["kpis"])

KPI_QUERY = """
    SELECT
        COUNT(h.encounter_key) AS total_hospitalizations,
        COUNT(DISTINCT h.patient_key) AS total_patients,
        COALESCE(SUM(r.readmitted_flag), 0) AS total_readmissions,
        COALESCE(AVG(r.readmitted_flag::float), 0) AS readmission_rate,
        COALESCE(AVG(r.readmitted_30_days::float), 0) AS readmitted_30_days_rate,
        COALESCE(AVG(h.time_in_hospital::float), 0) AS avg_time_in_hospital,
        COALESCE(AVG(h.num_medications::float), 0) AS avg_num_medications,
        COALESCE(AVG(h.number_diagnoses::float), 0) AS avg_number_diagnoses
    FROM warehouse.fact_hospitalization h
    JOIN warehouse.fact_readmission r ON r.encounter_key = h.encounter_key
"""


@router.get("/kpis", response_model=KPIResponse)
def get_kpis(engine: Engine = Depends(get_db_engine)) -> KPIResponse:
    with engine.connect() as connection:
        row = connection.execute(text(KPI_QUERY)).mappings().one()

    return KPIResponse(**dict(row))
