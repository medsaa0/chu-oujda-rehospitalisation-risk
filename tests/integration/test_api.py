"""
Tests d'integration de l'API FastAPI (Etape 18).

Necessite PostgreSQL demarre avec le pipeline complet deja execute
(Etapes 7 a 10), et le modele entraine (Etape 17) pour /api/predict.
"""

from fastapi.testclient import TestClient

from api.app.main import app

client = TestClient(app)


def test_health_reports_connected_database() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_kpis_returns_plausible_values() -> None:
    response = client.get("/api/kpis")

    assert response.status_code == 200

    body = response.json()
    assert body["total_hospitalizations"] > 0
    assert 0.0 <= body["readmitted_30_days_rate"] <= 1.0


def test_patients_pagination() -> None:
    response = client.get("/api/patients", params={"limit": 5, "offset": 0})

    assert response.status_code == 200

    body = response.json()
    assert body["limit"] == 5
    assert len(body["items"]) == 5
    assert body["total"] > 0


def test_hospitalizations_pagination() -> None:
    response = client.get(
        "/api/hospitalizations", params={"limit": 3, "offset": 0}
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 3


def test_readmissions_filter_by_readmitted_30_days() -> None:
    response = client.get(
        "/api/readmissions",
        params={"limit": 10, "readmitted_30_days": 1},
    )

    assert response.status_code == 200

    body = response.json()
    assert all(
        item["readmitted_30_days"] == 1 for item in body["items"]
    )


def test_data_quality_returns_recent_runs() -> None:
    response = client.get("/api/data-quality")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_pipeline_runs_returns_recent_runs() -> None:
    response = client.get("/api/pipeline-runs")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_predict_returns_a_risk_category() -> None:
    payload = {
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

    response = client.post("/api/predict", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert 0.0 <= body["predicted_probability"] <= 1.0
    assert body["predicted_risk_category"] in {"Low", "Medium", "High"}


def test_predict_rejects_invalid_payload() -> None:
    response = client.post("/api/predict", json={"time_in_hospital": 4})

    assert response.status_code == 422
