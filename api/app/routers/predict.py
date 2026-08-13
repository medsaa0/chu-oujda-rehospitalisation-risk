"""POST /api/predict : score une hospitalisation avec le modele ML (Etape 17)."""

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.app.dependencies import get_model_bundle
from api.app.schemas import PredictionRequest, PredictionResponse
from ml.training.train_models import CATEGORICAL_FEATURES
from src.utils.logging_config import get_logger

logger = get_logger("api_predict")

router = APIRouter(prefix="/api", tags=["predict"])


@router.post("/predict", response_model=PredictionResponse)
def predict_readmission_risk(payload: PredictionRequest) -> PredictionResponse:
    try:
        bundle = get_model_bundle()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    features = pd.DataFrame([payload.model_dump()])

    for column_name in CATEGORICAL_FEATURES:
        features[column_name] = features[column_name].astype(str)

    try:
        probability = float(bundle.pipeline.predict_proba(features)[0, 1])
    except Exception as error:
        logger.exception("Echec de la prediction : %s", error)
        raise HTTPException(
            status_code=422,
            detail=f"Impossible de scorer ces variables : {error}",
        ) from error

    return PredictionResponse(
        predicted_probability=round(probability, 4),
        predicted_risk_category=bundle.categorize(probability),
        model_name=bundle.model_name,
    )
