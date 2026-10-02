"""
VAYORA AI Service — Optimization & Recovery Pydantic Schemas (B3, B6)
"""
from __future__ import annotations

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# B3 — OR-Tools Optimization Schemas
# ─────────────────────────────────────────────

class OptRideSchema(BaseModel):
    ride_id: UUID
    driver_id: UUID
    available_seats: int = Field(..., ge=1)
    departure_time: datetime
    max_detour_minutes: int = 20
    price_per_seat: float = Field(..., ge=0)
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float


class OptPassengerSchema(BaseModel):
    passenger_id: UUID
    request_id: UUID
    seats_needed: int = Field(..., ge=1)
    requested_departure: datetime
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    max_price: Optional[float] = None
    wheelchair_required: bool = False
    # Pre-scored match scores per ride index [ride_index → int 0-100]
    match_scores: Dict[int, int] = Field(default_factory=dict)


class OptimizeRequest(BaseModel):
    """
    B3: Global optimization request.
    Typically called after B2 SmartMatch has scored all passenger-ride pairs.
    """
    rides: List[OptRideSchema] = Field(..., min_length=1)
    passengers: List[OptPassengerSchema] = Field(..., min_length=1)
    solver_timeout_seconds: int = Field(10, ge=1, le=60)
    experiment_id: Optional[str] = None


class AssignmentSchema(BaseModel):
    passenger_id: UUID
    request_id: UUID
    ride_id: UUID
    driver_id: UUID
    match_score: int
    seats_assigned: int
    is_optimal: bool


class OptimizationResponse(BaseModel):
    assignments: List[AssignmentSchema]
    total_passengers: int
    total_assigned: int
    total_unassigned: int
    solver_status: str
    solve_time_ms: float
    objective_value: int
    algorithm: str
    is_simulation: bool = True
    experiment_id: Optional[str] = None


# ─────────────────────────────────────────────
# B6 — RecoveryMatch Schemas
# ─────────────────────────────────────────────

class CancelledBookingSchema(BaseModel):
    booking_id: UUID
    passenger_id: UUID
    original_ride_id: UUID
    original_driver_id: UUID
    seats_booked: int = Field(..., ge=1)
    original_departure: datetime
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    total_price_paid: float


class BackupRideSchema(BaseModel):
    ride_id: UUID
    driver_id: UUID
    available_seats: int = Field(..., ge=1)
    departure_time: datetime
    price_per_seat: float
    max_detour_minutes: int = 20
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    driver_completed_rides: int = 0
    driver_cancellations: int = 0
    driver_avg_rating: Optional[float] = None
    journey_confidence_score: Optional[float] = None


class RecoveryRequest(BaseModel):
    """
    B6: RecoveryMatch request triggered on driver cancellation.
    Spring Boot calls this endpoint immediately when a ride is cancelled.
    """
    cancellation_id: Optional[UUID] = None
    original_ride_id: UUID
    original_driver_id: UUID
    affected_bookings: List[CancelledBookingSchema] = Field(..., min_length=1)
    backup_rides: List[BackupRideSchema]  # Can be empty — engine will report unrecoverable
    recovery_window_hours: float = Field(3.0, ge=0.5, le=12.0)
    top_k: int = Field(3, ge=1, le=10)
    experiment_id: Optional[str] = None


class RecoveryCandidateSchema(BaseModel):
    booking_id: UUID
    passenger_id: UUID
    backup_ride_id: UUID
    backup_driver_id: UUID
    recovery_score: float
    estimated_detour_mins: int
    price_difference: float
    time_difference_mins: float
    match_score: float
    urgency_bonus: float
    shap_contributions: Dict[str, float]
    reason: str
    is_simulation: bool = True


class PassengerRecoveryPlan(BaseModel):
    passenger_id: UUID
    booking_id: UUID
    candidates: List[RecoveryCandidateSchema]
    has_recovery: bool
    top_score: float = 0.0


class RecoveryResponse(BaseModel):
    """Complete recovery plan returned for a cancellation event."""
    cancellation_id: Optional[UUID]
    original_ride_id: UUID
    affected_passengers: int
    passenger_plans: List[PassengerRecoveryPlan]
    fully_recovered: int
    partially_recovered: int
    unrecoverable: int
    recovery_rate: float
    algorithm: str
    is_simulation: bool = True
    experiment_id: Optional[str] = None
    generated_at: datetime
