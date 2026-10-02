"""
VAYORA AI Service — EV Feasibility Router (B7)
POST /ai/ev/check  →  EV feasibility check + charging recommendation
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.demand_ev_schemas import (
    EVFeasibilityRequest, EVFeasibilityResponse, ChargingStationSchema
)
from app.services.ev_feasibility import (
    get_ev_engine,
    EVVehicleSpec, RouteProfile, ChargingStation
)
from app.services.persistence import save_prediction, log_event

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/ev/check",
    response_model=EVFeasibilityResponse,
    summary="B7: EV Feasibility — Can This EV Complete the Ride?",
    description=(
        "Checks whether an EV vehicle can complete a ride on its current State of Charge. "
        "Estimates energy consumption with terrain (ghat), highway, load, and temperature factors. "
        "If infeasible, recommends the nearest compatible charging station. "
        "All values are PUBLIC_CALIBRATION estimates — not guarantees. "
        "Experiment baseline B7."
    ),
    tags=["EV"],
)
async def check_ev_feasibility(
    request: EVFeasibilityRequest,
    db: AsyncSession = Depends(get_db),
) -> EVFeasibilityResponse:
    engine = get_ev_engine()

    ev_spec = EVVehicleSpec(
        vehicle_id=request.ev_spec.vehicle_id,
        battery_capacity_kwh=request.ev_spec.battery_capacity_kwh,
        consumption_per_km_kwh=request.ev_spec.consumption_per_km_kwh,
        current_soc_percentage=request.ev_spec.current_soc_percentage,
        supported_charger_types=request.ev_spec.supported_charger_types,
    )

    route = RouteProfile(
        ride_id=request.route.ride_id,
        origin_lat=request.route.origin_lat,
        origin_lng=request.route.origin_lng,
        dest_lat=request.route.dest_lat,
        dest_lng=request.route.dest_lng,
        distance_km=request.route.distance_km,
        duration_minutes=request.route.duration_minutes,
        has_ghat_section=request.route.has_ghat_section,
        is_highway=request.route.is_highway,
        passenger_count=request.route.passenger_count,
        ambient_temp_c=request.route.ambient_temp_c,
    )

    stations = [
        ChargingStation(
            station_id=s.station_id,
            name=s.name,
            lat=s.lat,
            lng=s.lng,
            charger_types=s.charger_types,
            max_kw=s.max_kw,
            is_operational=s.is_operational,
        )
        for s in request.nearby_stations
    ]

    try:
        result = engine.check_feasibility(ev_spec, route, stations, request.experiment_id)
    except Exception as exc:
        logger.exception("EV feasibility check failed")
        raise HTTPException(status_code=500, detail=f"EV engine error: {exc}")

    # Persist prediction for B7 tracking
    await save_prediction(
        db,
        model_name="EVFeasibility",
        model_version=result.model_version,
        target_entity_id=result.ride_id,
        target_entity_type="RIDE",
        prediction_type="EV_FEASIBILITY",
        prediction_value=float(result.feasibility_score),
        features_json={
            "vehicle_id": str(result.vehicle_id),
            "distance_km": route.distance_km,
            "current_soc": ev_spec.current_soc_percentage,
            "required_kwh": result.estimated_kwh_required,
            "available_kwh": result.available_kwh,
            "charging_required": result.charging_required,
        },
        shap_values={k: v for k, v in result.energy_breakdown.items() if isinstance(v, float)},
        experiment_id=request.experiment_id,
    )

    await log_event(
        db,
        event_type="EV_FEASIBILITY_CHECK",
        ride_id=result.ride_id,
        payload={
            "vehicle_id": str(result.vehicle_id),
            "is_feasible": result.is_feasible,
            "feasibility_score": result.feasibility_score,
            "charging_required": result.charging_required,
            "experiment_id": request.experiment_id,
        },
    )

    # Build charging station schema if recommended
    rec_station_schema = None
    if result.recommended_station:
        s = result.recommended_station
        rec_station_schema = ChargingStationSchema(
            station_id=s.station_id,
            name=s.name,
            lat=s.lat,
            lng=s.lng,
            charger_types=s.charger_types,
            max_kw=s.max_kw,
            is_operational=s.is_operational,
            distance_from_route_km=s.distance_from_route_km,
        )

    return EVFeasibilityResponse(
        vehicle_id=result.vehicle_id,
        ride_id=result.ride_id,
        estimated_kwh_required=result.estimated_kwh_required,
        available_kwh=result.available_kwh,
        safety_buffer_kwh=result.safety_buffer_kwh,
        is_feasible=result.is_feasible,
        feasibility_score=result.feasibility_score,
        infeasibility_reason=result.infeasibility_reason,
        charging_required=result.charging_required,
        recommended_station=rec_station_schema,
        charging_time_minutes=result.charging_time_minutes,
        kwh_to_charge=result.kwh_to_charge,
        updated_eta_minutes=result.updated_eta_minutes,
        energy_breakdown=result.energy_breakdown,
        explanation=result.explanation,
        model_version=result.model_version,
        data_source=result.data_source,
        is_simulation=result.is_simulation,
        experiment_id=request.experiment_id,
    )
