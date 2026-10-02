"""
VAYORA AI Service — RecoveryMatch Router (B6)
POST /ai/recovery/find  →  Find backup rides after driver cancellation
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.optimization_schemas import (
    RecoveryRequest, RecoveryResponse,
    PassengerRecoveryPlan, RecoveryCandidateSchema
)
from app.services.recovery import (
    get_recovery_engine,
    CancelledBooking, BackupRide
)
from app.services.persistence import log_event

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/recovery/find",
    response_model=RecoveryResponse,
    summary="B6: RecoveryMatch — Find Backup Rides After Cancellation",
    description=(
        "VAYORA's signature feature. When a driver cancels a ride, this endpoint "
        "immediately finds and ranks backup rides for each affected passenger. "
        "Returns a per-passenger ranked list of recovery candidates with SHAP explanations. "
        "Passengers are always notified, even if no recovery is found (transparency). "
        "All outputs labeled SIMULATION. Experiment baseline B6."
    ),
    tags=["Recovery"],
)
async def find_recovery(
    request: RecoveryRequest,
    db: AsyncSession = Depends(get_db),
) -> RecoveryResponse:
    engine = get_recovery_engine(window_hours=request.recovery_window_hours)

    # Convert schema → internal data classes
    affected_bookings = [
        CancelledBooking(
            booking_id=b.booking_id,
            passenger_id=b.passenger_id,
            original_ride_id=b.original_ride_id,
            original_driver_id=b.original_driver_id,
            seats_booked=b.seats_booked,
            original_departure=b.original_departure,
            pickup_lat=b.pickup_lat,
            pickup_lng=b.pickup_lng,
            dropoff_lat=b.dropoff_lat,
            dropoff_lng=b.dropoff_lng,
            total_price_paid=b.total_price_paid,
        )
        for b in request.affected_bookings
    ]

    backup_rides = [
        BackupRide(
            ride_id=r.ride_id,
            driver_id=r.driver_id,
            available_seats=r.available_seats,
            departure_time=r.departure_time,
            price_per_seat=r.price_per_seat,
            max_detour_minutes=r.max_detour_minutes,
            origin_lat=r.origin_lat,
            origin_lng=r.origin_lng,
            dest_lat=r.dest_lat,
            dest_lng=r.dest_lng,
            driver_completed_rides=r.driver_completed_rides,
            driver_cancellations=r.driver_cancellations,
            driver_avg_rating=r.driver_avg_rating,
            journey_confidence_score=r.journey_confidence_score,
        )
        for r in request.backup_rides
    ]

    try:
        plan = engine.find_recovery(
            affected_bookings=affected_bookings,
            backup_rides=backup_rides,
            now=datetime.now(timezone.utc),
            original_ride_id=request.original_ride_id,
            original_driver_id=request.original_driver_id,
            cancellation_id=request.cancellation_id,
            experiment_id=request.experiment_id,
            top_k=request.top_k,
        )
    except Exception as exc:
        logger.exception("RecoveryMatch failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RecoveryMatch error: {str(exc)}"
        )

    # Build per-passenger plans for the response
    passenger_plans = []
    for booking, candidates in zip(affected_bookings, plan.recovery_plans):
        schema_candidates = [
            RecoveryCandidateSchema(
                booking_id=c.booking_id,
                passenger_id=c.passenger_id,
                backup_ride_id=c.backup_ride_id,
                backup_driver_id=c.backup_driver_id,
                recovery_score=c.recovery_score,
                estimated_detour_mins=c.estimated_detour_mins,
                price_difference=c.price_difference,
                time_difference_mins=c.time_difference_mins,
                match_score=c.match_score,
                urgency_bonus=c.urgency_bonus,
                shap_contributions=c.shap_contributions,
                reason=c.reason,
                is_simulation=c.is_simulation,
            )
            for c in candidates
        ]
        has_recovery = len(candidates) > 0
        top_score = candidates[0].recovery_score if candidates else 0.0
        passenger_plans.append(PassengerRecoveryPlan(
            passenger_id=booking.passenger_id,
            booking_id=booking.booking_id,
            candidates=schema_candidates,
            has_recovery=has_recovery,
            top_score=top_score,
        ))

    # Log KPI event for research tracking
    await log_event(
        db,
        event_type="RECOVERY_ATTEMPTED",
        ride_id=request.original_ride_id,
        payload={
            "original_driver_id": str(request.original_driver_id),
            "affected_passengers": plan.affected_passengers,
            "fully_recovered": plan.fully_recovered,
            "unrecoverable": plan.unrecoverable,
            "recovery_rate": plan.recovery_rate,
            "algorithm": plan.algorithm,
            "experiment_id": request.experiment_id,
        },
    )

    return RecoveryResponse(
        cancellation_id=request.cancellation_id,
        original_ride_id=request.original_ride_id,
        affected_passengers=plan.affected_passengers,
        passenger_plans=passenger_plans,
        fully_recovered=plan.fully_recovered,
        partially_recovered=plan.partially_recovered,
        unrecoverable=plan.unrecoverable,
        recovery_rate=plan.recovery_rate,
        algorithm=plan.algorithm,
        is_simulation=plan.is_simulation,
        experiment_id=plan.experiment_id,
        generated_at=plan.generated_at,
    )
