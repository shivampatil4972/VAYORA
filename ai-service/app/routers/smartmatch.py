"""
VAYORA AI Service — SmartMatch Router
POST /ai/match/b1  →  B1 Rule-Based Matching
POST /ai/match/b2  →  B2 SmartMatch (Two-Sided Matching)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.ai_schemas import SmartMatchRequest, SmartMatchResponse
from app.services.smartmatch import get_b1_engine, get_b2_engine
from app.services.persistence import save_prediction, log_event

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_match(
    request: SmartMatchRequest,
    algorithm: str,
    db: AsyncSession,
) -> SmartMatchResponse:
    """Shared logic: score, rank, persist, return."""

    engine = get_b1_engine() if algorithm == "B1_RULE_BASED" else get_b2_engine()

    try:
        response = engine.rank_candidates(request)
    except Exception as exc:
        logger.exception("SmartMatch scoring failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching engine error: {str(exc)}"
        )

    # Persist top match score to ml_predictions (non-blocking best effort)
    if response.ranked_matches:
        top = response.ranked_matches[0]
        await save_prediction(
            db,
            model_name="SmartMatch",
            model_version=algorithm,
            target_entity_id=top.ride_id,
            target_entity_type="RIDE",
            prediction_type="MATCH_SCORE",
            prediction_value=float(top.composite_score),
            features_json={
                "passenger_id": str(request.passenger_id),
                "seats_needed": request.seats_needed,
                "candidates_count": len(request.candidates),
            },
            shap_values=top.shap_contributions,
            experiment_id=request.experiment_id,
        )

    # Log event for KPI tracking
    await log_event(
        db,
        event_type="MATCH_GENERATED",
        user_id=request.passenger_id,
        payload={
            "algorithm": algorithm,
            "total_candidates": response.total_candidates,
            "matches_returned": len(response.ranked_matches),
            "experiment_id": request.experiment_id,
        },
    )

    return response


@router.post(
    "/match/b1",
    response_model=SmartMatchResponse,
    summary="B1: Rule-Based Ride Matching",
    description=(
        "Applies deterministic rule-based scoring to rank candidate rides. "
        "Uses geographic proximity, time alignment, price, and reliability metrics. "
        "Experiment baseline B1."
    ),
    tags=["SmartMatch"],
)
async def b1_match(
    request: SmartMatchRequest,
    db: AsyncSession = Depends(get_db),
) -> SmartMatchResponse:
    request.experiment_id = request.experiment_id or "B1"
    return await _run_match(request, "B1_RULE_BASED", db)


@router.post(
    "/match/b2",
    response_model=SmartMatchResponse,
    summary="B2: SmartMatch — Two-Sided Matching",
    description=(
        "Two-sided matching with reliability-weighted composite scoring. "
        "Includes SHAP-style explanations for every recommendation (Explainable AI). "
        "Passenger always retains final choice. "
        "Experiment baseline B2."
    ),
    tags=["SmartMatch"],
)
async def b2_match(
    request: SmartMatchRequest,
    db: AsyncSession = Depends(get_db),
) -> SmartMatchResponse:
    request.experiment_id = request.experiment_id or "B2"
    return await _run_match(request, "B2_SMARTMATCH", db)
