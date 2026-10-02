"""
VAYORA AI Service — Optimization Router (B3)
POST /ai/optimize  →  OR-Tools global ride assignment
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.optimization_schemas import (
    OptimizeRequest, OptimizationResponse, AssignmentSchema
)
from app.services.optimizer import (
    get_optimizer, OptRide, OptPassenger
)
from app.services.persistence import log_event

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/optimize",
    response_model=OptimizationResponse,
    summary="B3: OR-Tools Global Ride Assignment Optimization",
    description=(
        "Globally optimizes the assignment of passengers to rides using CP-SAT constraint "
        "programming. Maximizes total SmartMatch score across all passengers simultaneously, "
        "subject to seat capacity and detour constraints. "
        "Falls back to greedy matching if OR-Tools solver is unavailable. "
        "Experiment baseline B3."
    ),
    tags=["Optimization"],
)
async def optimize_assignments(
    request: OptimizeRequest,
    db: AsyncSession = Depends(get_db),
) -> OptimizationResponse:
    optimizer = get_optimizer(timeout=request.solver_timeout_seconds)

    # Convert schema objects to internal data classes
    rides = [
        OptRide(
            ride_id=r.ride_id,
            driver_id=r.driver_id,
            available_seats=r.available_seats,
            departure_time=r.departure_time,
            max_detour_minutes=r.max_detour_minutes,
            price_per_seat=r.price_per_seat,
            origin_lat=r.origin_lat,
            origin_lng=r.origin_lng,
            dest_lat=r.dest_lat,
            dest_lng=r.dest_lng,
        )
        for r in request.rides
    ]

    passengers = [
        OptPassenger(
            passenger_id=p.passenger_id,
            request_id=p.request_id,
            seats_needed=p.seats_needed,
            requested_departure=p.requested_departure,
            origin_lat=p.origin_lat,
            origin_lng=p.origin_lng,
            dest_lat=p.dest_lat,
            dest_lng=p.dest_lng,
            max_price=p.max_price,
            wheelchair_required=p.wheelchair_required,
            match_scores=p.match_scores,
        )
        for p in request.passengers
    ]

    try:
        result = optimizer.optimize(rides, passengers, request.experiment_id)
    except Exception as exc:
        logger.exception("Optimization failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization error: {str(exc)}"
        )

    # Log KPI event
    await log_event(
        db,
        event_type="OPTIMIZATION_RUN",
        payload={
            "algorithm": result.algorithm,
            "solver_status": result.solver_status,
            "total_passengers": result.total_passengers,
            "total_assigned": result.total_assigned,
            "objective_value": result.objective_value,
            "solve_time_ms": result.solve_time_ms,
            "experiment_id": request.experiment_id,
        },
    )

    return OptimizationResponse(
        assignments=[
            AssignmentSchema(
                passenger_id=a.passenger_id,
                request_id=a.request_id,
                ride_id=a.ride_id,
                driver_id=a.driver_id,
                match_score=a.match_score,
                seats_assigned=a.seats_assigned,
                is_optimal=a.is_optimal,
            )
            for a in result.assignments
        ],
        total_passengers=result.total_passengers,
        total_assigned=result.total_assigned,
        total_unassigned=result.total_unassigned,
        solver_status=result.solver_status,
        solve_time_ms=result.solve_time_ms,
        objective_value=result.objective_value,
        algorithm=result.algorithm,
        is_simulation=result.is_simulation,
        experiment_id=result.experiment_id,
    )
