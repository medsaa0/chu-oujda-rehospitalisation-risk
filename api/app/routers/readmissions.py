"""GET /api/readmissions : liste paginee du Mart Reheospitalisation."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.engine import Engine

from api.app.dependencies import get_db_engine

router = APIRouter(prefix="/api", tags=["readmissions"])


@router.get("/readmissions")
def list_readmissions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    readmitted_30_days: int | None = Query(default=None, ge=0, le=1),
    engine: Engine = Depends(get_db_engine),
) -> dict[str, Any]:
    where_clause = ""
    parameters: dict[str, Any] = {"limit": limit, "offset": offset}

    if readmitted_30_days is not None:
        where_clause = "WHERE readmitted_30_days = :readmitted_30_days"
        parameters["readmitted_30_days"] = readmitted_30_days

    query = text(
        f"""
        SELECT *
        FROM marts.mart_readmission
        {where_clause}
        ORDER BY encounter_key
        LIMIT :limit OFFSET :offset
        """
    )

    count_query = text(
        f"SELECT COUNT(*) FROM marts.mart_readmission {where_clause}"
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
