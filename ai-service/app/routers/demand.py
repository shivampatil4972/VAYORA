"""
VAYORA AI Service — DemandAI Router (B5)
POST /ai/demand/predict   →  Zone demand prediction + gap scores
POST /ai/demand/nudge     →  Driver repositioning nudges
POST /ai/demand/heatmap   →  Demand heatmap for frontend
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.demand_ev_schemas import (
    DemandPredictRequest, DemandPredictResponse, DemandPredictionSchema,
    NudgeRequest, NudgeResponse, DriverNudgeSchema,
    HeatmapResponse, HeatmapCellSchema,
)
from app.services.demand import (
    get_demand_engine, HistoricalRecord, lat_lng_to_zone
)
from app.services.persistence import log_event

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_internal_record(r) -> HistoricalRecord:
    return HistoricalRecord(
        zone_id=r.zone_id,
        hour_of_day=r.hour_of_day,
        day_of_week=r.day_of_week,
        total_searches=r.total_searches,
        fulfilled_searches=r.fulfilled_searches,
        unfulfilled_searches=r.unfulfilled_searches,
        total_rides_offered=r.total_rides_offered,
    )


@router.post(
    "/demand/predict",
    response_model=DemandPredictResponse,
    summary="B5: DemandAI — Zone-Level Demand Prediction",
    description=(
        "Predicts supply-demand gaps for geographic zones. "
        "Key signal: zero-result searches (unfulfilled ride requests). "
        "All predictions labeled SIMULATION. Experiment baseline B5."
    ),
    tags=["DemandAI"],
)
async def predict_demand(
    request: DemandPredictRequest,
    db: AsyncSession = Depends(get_db),
) -> DemandPredictResponse:
    engine = get_demand_engine()

    records = [_to_internal_record(r) for r in request.records]

    try:
        predictions = engine.predict_zone_demand(records, request.target_hour, request.target_day_of_week)
    except Exception as exc:
        logger.exception("DemandAI prediction failed")
        raise HTTPException(status_code=500, detail=f"DemandAI error: {exc}")

    high_gap_zones = sum(1 for p in predictions if p.gap_score > 0.5)

    await log_event(
        db,
        event_type="DEMAND_PREDICTION_RUN",
        payload={
            "zones": len(predictions),
            "high_gap_zones": high_gap_zones,
            "hour": request.target_hour,
            "dow": request.target_day_of_week,
            "experiment_id": request.experiment_id,
        },
    )

    return DemandPredictResponse(
        predictions=[
            DemandPredictionSchema(
                zone_id=p.zone_id,
                center_lat=p.center_lat,
                center_lng=p.center_lng,
                prediction_hour=p.prediction_hour,
                day_of_week=p.day_of_week,
                expected_demand=p.expected_demand,
                expected_supply=p.expected_supply,
                gap_score=p.gap_score,
                fulfillment_rate=p.fulfillment_rate,
                confidence=p.confidence,
                data_source=p.data_source,
                model_version=p.model_version,
            )
            for p in predictions
        ],
        total_zones=len(predictions),
        high_gap_zones=high_gap_zones,
        is_simulation=True,
        experiment_id=request.experiment_id,
        generated_at=datetime.now(timezone.utc),
    )


@router.post(
    "/demand/nudge",
    response_model=NudgeResponse,
    summary="B5: DemandAI — Driver Repositioning Nudges",
    description=(
        "Generates personalized driver nudges to reposition toward high-demand zones. "
        "Nudges are suggestions only — driver retains full autonomy (AI Ethics). "
        "All nudges labeled SIMULATION."
    ),
    tags=["DemandAI"],
)
async def generate_nudges(
    request: NudgeRequest,
    db: AsyncSession = Depends(get_db),
) -> NudgeResponse:
    engine = get_demand_engine()

    # Convert schemas to internal DemandPrediction objects
    from app.services.demand import DemandPrediction
    predictions = [
        DemandPrediction(
            zone_id=p.zone_id,
            center_lat=p.center_lat,
            center_lng=p.center_lng,
            prediction_hour=p.prediction_hour,
            day_of_week=p.day_of_week,
            expected_demand=p.expected_demand,
            expected_supply=p.expected_supply,
            gap_score=p.gap_score,
            fulfillment_rate=p.fulfillment_rate,
            confidence=p.confidence,
        )
        for p in request.predictions
    ]

    try:
        nudges = engine.generate_nudges(
            predictions=predictions,
            driver_id=request.driver_id,
            driver_lat=request.driver_lat,
            driver_lng=request.driver_lng,
            max_nudge_km=request.max_nudge_km,
            top_n=request.top_n,
        )
    except Exception as exc:
        logger.exception("Nudge generation failed")
        raise HTTPException(status_code=500, detail=f"Nudge error: {exc}")

    return NudgeResponse(
        driver_id=request.driver_id,
        nudges=[
            DriverNudgeSchema(
                driver_id=n.driver_id,
                current_zone=n.current_zone,
                target_zone=n.target_zone,
                target_lat=n.target_lat,
                target_lng=n.target_lng,
                distance_km=n.distance_km,
                demand_gap_score=n.demand_gap_score,
                expected_demand=n.expected_demand,
                nudge_message=n.nudge_message,
                urgency=n.urgency,
                is_simulation=n.is_simulation,
            )
            for n in nudges
        ],
        is_simulation=True,
    )


@router.post(
    "/demand/heatmap",
    response_model=HeatmapResponse,
    summary="B5: DemandAI — Demand Heatmap",
    description="Returns a normalized demand heatmap grid for frontend map visualization.",
    tags=["DemandAI"],
)
async def get_heatmap(
    request: DemandPredictRequest,
    db: AsyncSession = Depends(get_db),
) -> HeatmapResponse:
    engine = get_demand_engine()
    records = [_to_internal_record(r) for r in request.records]

    try:
        predictions = engine.predict_zone_demand(records, request.target_hour, request.target_day_of_week)
        heatmap = engine.generate_heatmap(predictions)
    except Exception as exc:
        logger.exception("Heatmap generation failed")
        raise HTTPException(status_code=500, detail=f"Heatmap error: {exc}")

    return HeatmapResponse(
        cells=[
            HeatmapCellSchema(
                lat=c.lat, lng=c.lng,
                demand_score=c.demand_score,
                gap_score=c.gap_score,
                label=c.label,
            )
            for c in heatmap.cells
        ],
        generated_at=heatmap.generated_at,
        hour=heatmap.hour,
        day_of_week=heatmap.day_of_week,
        is_simulation=heatmap.is_simulation,
    )
