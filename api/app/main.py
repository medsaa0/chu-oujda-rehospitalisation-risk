"""
API FastAPI de la plateforme CHU Oujda (Etape 18).

Expose les KPIs, les Data Marts et le modele predictif construits aux
Etapes 9 a 17.

Lancement :
    uvicorn api.app.main:app --reload
"""

from fastapi import FastAPI

from api.app.routers import (
    data_quality,
    health,
    hospitalizations,
    kpis,
    patients,
    pipeline_runs,
    predict,
    readmissions,
)

app = FastAPI(
    title="CHU Oujda — Risque de reheospitalisation",
    description=(
        "API exposant les indicateurs, les Data Marts et le modele "
        "predictif de reheospitalisation a 30 jours."
    ),
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(kpis.router)
app.include_router(patients.router)
app.include_router(hospitalizations.router)
app.include_router(readmissions.router)
app.include_router(data_quality.router)
app.include_router(pipeline_runs.router)
app.include_router(predict.router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"docs": "/docs"}
