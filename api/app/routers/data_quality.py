"""GET /api/data-quality : historique des controles qualite (Etape 6)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.engine import Engine

from api.app.dependencies import get_db_engine
from api.app.schemas import DataQualityRunResponse

router = APIRouter(prefix="/api", tags=["data-quality"])

DATA_QUALITY_QUERY = """
    SELECT
        quality_run_id,
        raw_file_name,
        status,
        total_rows,
        valid_rows,
        rejected_rows,
        total_violations,
        duplicate_rows,
        valid_rate_percent,
        started_at::text,
        finished_at::text
    FROM marts.mart_quality
    ORDER BY started_at DESC
    LIMIT :limit
"""


@router.get("/data-quality", response_model=list[DataQualityRunResponse])
def list_data_quality_runs(
    limit: int = Query(default=20, ge=1, le=200),
    engine: Engine = Depends(get_db_engine),
) -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(DATA_QUALITY_QUERY), {"limit": limit}
        ).mappings().all()

    return [dict(row) for row in rows]
