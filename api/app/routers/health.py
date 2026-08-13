"""GET /health : verifie que l'API et la base de donnees repondent."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from api.app.dependencies import get_db_engine
from api.app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(engine: Engine = Depends(get_db_engine)) -> HealthResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        database_status = "unavailable"

    return HealthResponse(status="ok", database=database_status)
