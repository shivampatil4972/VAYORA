"""
VAYORA AI Service — ReliabilityAI Router (B4)
POST /ai/reliability/predict  →  Predict P(cancel) for a driver-ride pair
POST /ai/reliability/batch    →  Batch prediction for multiple driver-ride pairs
"""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.ai_schemas import ReliabilityFeatures, ReliabilityPrediction
from app.services.reliability import get_reliability_engine
from app.services.persistence import save_prediction

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/reliability/predict",
    response_model=ReliabilityPrediction,
    summary="B4: ReliabilityAI — Predict Driver Cancellation Probability",
    description=(
        "Predicts P(cancel) for a specific driver-ride pair using factual historical metrics. "
        "No character inferences are made. All outputs are labeled as SIMULATION data. "
        "This is a prediction, not a guarantee. Experiment baseline B4."
    ),
    tags=["ReliabilityAI"],
)
async def predict_reliability(
    features: ReliabilityFeatures,
    db: AsyncSession = Depends(get_db),
) -> ReliabilityPrediction:
    engine = get_reliability_engine()

    try:
        prediction = engine.predict(features)
    except Exception as exc:
        logger.exception("ReliabilityAI prediction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ReliabilityAI error: {str(exc)}"
        )

    # Persist prediction for research KPI tracking
    await save_prediction(
        db,
        model_name="ReliabilityAI",
        model_version=prediction.model_version,
        target_entity_id=features.ride_id,
        target_entity_type="RIDE",
        prediction_type="P_CANCEL",
        prediction_value=float(prediction.p_cancel),
        features_json={
            "driver_id": str(features.driver_id),
            "completed_rides": features.completed_rides,
            "cancellations": features.cancellations,
            "distance_km": features.distance_km,
            "hour_of_day": features.hour_of_day,
            "day_of_week": features.day_of_week,
        },
        shap_values=prediction.shap_contributions,
        experiment_id=features.experiment_id,
    )

    return prediction


@router.post(
    "/reliability/batch",
    response_model=List[ReliabilityPrediction],
    summary="B4: ReliabilityAI — Batch Prediction",
    description=(
        "Batch predict P(cancel) for multiple driver-ride pairs. "
        "Used by the SmartMatch pipeline to enrich candidates before ranking."
    ),
    tags=["ReliabilityAI"],
)
async def predict_reliability_batch(
    features_list: List[ReliabilityFeatures],
    db: AsyncSession = Depends(get_db),
) -> List[ReliabilityPrediction]:
    if len(features_list) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 50 items."
        )

    engine = get_reliability_engine()
    results: List[ReliabilityPrediction] = []

    for features in features_list:
        try:
            prediction = engine.predict(features)
            results.append(prediction)
            # Persist each prediction (best-effort)
            await save_prediction(
                db,
                model_name="ReliabilityAI",
                model_version=prediction.model_version,
                target_entity_id=features.ride_id,
                target_entity_type="RIDE",
                prediction_type="P_CANCEL",
                prediction_value=float(prediction.p_cancel),
                experiment_id=features.experiment_id,
            )
        except Exception as exc:
            logger.warning("Skipping ride %s in batch: %s", features.ride_id, exc)

    return results
