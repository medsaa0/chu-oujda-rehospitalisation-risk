"""GET /api/pipeline-runs : historique des executions ETL (Etape 7)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.engine import Engine

from api.app.dependencies import get_db_engine
from api.app.schemas import PipelineRunResponse

router = APIRouter(prefix="/api", tags=["pipeline-runs"])

PIPELINE_RUNS_QUERY = """
    SELECT
        id AS run_id,
        status,
        target_schema,
        target_table,
        input_rows,
        output_rows,
        started_at::text,
        finished_at::text,
        error_message
    FROM etl_runs
    ORDER BY started_at DESC
    LIMIT :limit
"""


@router.get("/pipeline-runs", response_model=list[PipelineRunResponse])
def list_pipeline_runs(
    limit: int = Query(default=20, ge=1, le=200),
    engine: Engine = Depends(get_db_engine),
) -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(PIPELINE_RUNS_QUERY), {"limit": limit}
        ).mappings().all()

    return [dict(row) for row in rows]
