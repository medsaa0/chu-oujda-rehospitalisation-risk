"""GET /api/hospitalizations : liste paginee du Mart Hospitalisations."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.engine import Engine

from api.app.dependencies import get_db_engine

router = APIRouter(prefix="/api", tags=["hospitalizations"])


@router.get("/hospitalizations")
def list_hospitalizations(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    engine: Engine = Depends(get_db_engine),
) -> dict[str, Any]:
    query = text(
        """
        SELECT *
        FROM marts.mart_hospitalizations
        ORDER BY encounter_key
        LIMIT :limit OFFSET :offset
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query, {"limit": limit, "offset": offset}
        ).mappings().all()

        total = connection.execute(
            text("SELECT COUNT(*) FROM marts.mart_hospitalizations")
        ).scalar_one()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [dict(row) for row in rows],
    }
