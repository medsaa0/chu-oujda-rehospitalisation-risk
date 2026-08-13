"""GET /api/patients : liste paginee du Mart Patients."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.engine import Engine

from api.app.dependencies import get_db_engine

router = APIRouter(prefix="/api", tags=["patients"])


@router.get("/patients")
def list_patients(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    gender: str | None = None,
    race: str | None = None,
    engine: Engine = Depends(get_db_engine),
) -> dict[str, Any]:
    conditions = []
    parameters: dict[str, Any] = {"limit": limit, "offset": offset}

    if gender is not None:
        conditions.append("gender = :gender")
        parameters["gender"] = gender

    if race is not None:
        conditions.append("race = :race")
        parameters["race"] = race

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = text(
        f"""
        SELECT *
        FROM marts.mart_patients
        {where_clause}
        ORDER BY patient_key
        LIMIT :limit OFFSET :offset
        """
    )

    count_query = text(
        f"SELECT COUNT(*) FROM marts.mart_patients {where_clause}"
    )

    with engine.connect() as connection:
        rows = connection.execute(query, parameters).mappings().all()
        total = connection.execute(count_query, parameters).scalar_one()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [dict(row) for row in rows],
    }
