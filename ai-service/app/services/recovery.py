"""
VAYORA AI Service — RecoveryMatch Engine (B6)
===============================================
VAYORA's SIGNATURE FEATURE.

When a driver cancels a ride, RecoveryMatch automatically:
  1. Identifies all affected passengers (confirmed bookings on the cancelled ride)
  2. Finds candidate backup rides that could absorb each passenger
  3. Scores and ranks backup options using SmartMatch + time urgency
  4. Returns a ranked recovery plan for immediate passenger notification

Research Baseline B6 = B5 (DemandAI) + RecoveryMatch

Recovery SLA:
  - Recovery candidates must be identified within 60 seconds of cancellation
  - Only rides departing AFTER the cancellation time are eligible
  - Rides must have departure within recovery_window_hours of original departure
  - Passenger is ALWAYS notified, even if no recovery found (transparency)

All outputs labeled SIMULATION per research data source labeling policy.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from uuid import UUID

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────

@dataclass
class CancelledBooking:
    """A passenger booking affected by a driver cancellation."""
    booking_id: UUID
    passenger_id: UUID
    original_ride_id: UUID
    original_driver_id: UUID
    seats_booked: int
    original_departure: datetime
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    total_price_paid: float


@dataclass
class BackupRide:
    """A candidate backup ride that could replace the cancelled one."""
    ride_id: UUID
    driver_id: UUID
    available_seats: int
    departure_time: datetime
    price_per_seat: float
    max_detour_minutes: int
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    driver_completed_rides: int = 0
    driver_cancellations: int = 0
    driver_avg_rating: Optional[float] = None
    journey_confidence_score: Optional[float] = None


@dataclass
class RecoveryCandidate:
    """A scored and ranked backup ride for one affected passenger."""
    booking_id: UUID
    passenger_id: UUID
    backup_ride_id: UUID
    backup_driver_id: UUID
    recovery_score: float           # 0.0–1.0 composite
    estimated_detour_mins: int
    price_difference: float         # negative = cheaper, positive = more expensive
    time_difference_mins: float     # departure shift from original
    match_score: float              # SmartMatch component
    urgency_bonus: float            # Higher if fewer alternatives available
    shap_contributions: Dict[str, float]
    reason: str
    is_simulation: bool = True


@dataclass
class RecoveryPlan:
    """Full recovery plan for a cancellation event."""
    cancellation_id: Optional[UUID]
    original_ride_id: UUID
    original_driver_id: UUID
    affected_passengers: int
    recovery_plans: List[List[RecoveryCandidate]]   # One list per passenger
    fully_recovered: int            # Passengers with ≥1 candidate
    partially_recovered: int        # Passengers with candidates but not ideal
    unrecoverable: int              # Passengers with no candidates found
    recovery_rate: float            # fully_recovered / affected_passengers
    algorithm: str = "B6_RECOVERYMATCH"
    is_simulation: bool = True
    experiment_id: Optional[str] = None
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────
# Scoring utilities
# ─────────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _score_proximity(backup: BackupRide, booking: CancelledBooking, radius_km: float = 10.0) -> float:
    """How close is the backup ride's route to the passenger's pickup/dropoff?"""
    pickup_dist = _haversine_km(
        booking.pickup_lat, booking.pickup_lng,
        backup.origin_lat, backup.origin_lng
    )
    dropoff_dist = _haversine_km(
        booking.dropoff_lat, booking.dropoff_lng,
        backup.dest_lat, backup.dest_lng
    )
    pickup_score = math.exp(-pickup_dist / radius_km)
    dropoff_score = math.exp(-dropoff_dist / radius_km)
    return round(0.6 * pickup_score + 0.4 * dropoff_score, 4)


def _score_time_urgency(
    backup: BackupRide,
    booking: CancelledBooking,
    now: datetime,
    recovery_window_hours: float = 3.0,
) -> tuple[float, float]:
    """
    Score temporal alignment of the backup ride.
    Returns (time_score, time_difference_mins).
    Higher score = closer to original departure = better for passenger.
    """
    orig_ts = booking.original_departure
    backup_ts = backup.departure_time
    if orig_ts.tzinfo is None:
        orig_ts = orig_ts.replace(tzinfo=timezone.utc)
    if backup_ts.tzinfo is None:
        backup_ts = backup_ts.replace(tzinfo=timezone.utc)

    # Only future rides are eligible
    if backup_ts <= now:
        return 0.0, float('inf')

    diff_hours = abs((backup_ts - orig_ts).total_seconds()) / 3600.0
    diff_mins = (backup_ts - orig_ts).total_seconds() / 60.0

    # Gaussian decay within window
    sigma = recovery_window_hours / 2.0
    time_score = math.exp(-(diff_hours ** 2) / (2 * sigma ** 2))
    return round(time_score, 4), round(diff_mins, 1)


def _score_reliability(backup: BackupRide) -> float:
    """Bayesian-smoothed completion rate (same as SmartMatch reliability scorer)."""
    total = backup.driver_completed_rides + backup.driver_cancellations
    prior_completions = 17
    prior_total = 20
    rate = (backup.driver_completed_rides + prior_completions) / (total + prior_total)
    rating_boost = 0.0
    if backup.driver_avg_rating is not None:
        rating_boost = max(0.0, (backup.driver_avg_rating - 3.0) / 10.0)
    return round(min(1.0, rate + rating_boost), 4)


def _score_price(backup: BackupRide, booking: CancelledBooking) -> tuple[float, float]:
    """
    Score how affordable the backup is.
    Returns (price_score, price_difference_per_seat).
    """
    diff = backup.price_per_seat - (booking.total_price_paid / max(booking.seats_booked, 1))
    # Score: 1.0 if same price or cheaper, decays if more expensive
    price_score = max(0.0, 1.0 - max(0.0, diff) / 500.0)
    return round(price_score, 4), round(diff, 2)


def _estimate_detour(backup: BackupRide, booking: CancelledBooking) -> int:
    """
    Estimate detour minutes to pick up the passenger from their location.
    Uses haversine distance as a proxy (assumes ~30 km/h urban speed).
    """
    pickup_dist_km = _haversine_km(
        backup.origin_lat, backup.origin_lng,
        booking.pickup_lat, booking.pickup_lng
    )
    detour_mins = int((pickup_dist_km / 30.0) * 60)  # ~30 km/h
    return min(detour_mins, backup.max_detour_minutes * 2)  # cap at 2x max


# ─────────────────────────────────────────────────────────────────
# RecoveryMatch Engine
# ─────────────────────────────────────────────────────────────────

class RecoveryMatchEngine:
    """
    Scores and ranks backup rides for affected passengers after a cancellation.

    Composite recovery score = weighted combination of:
      - Proximity (pickup/dropoff geo alignment)    35%
      - Time alignment to original departure        25%
      - Driver reliability                          25%
      - Price similarity                            10%
      - Urgency bonus (fewer alternatives = higher) 5%
    """

    WEIGHTS = {
        "proximity": 0.35,
        "time": 0.25,
        "reliability": 0.25,
        "price": 0.10,
        "urgency": 0.05,
    }

    def __init__(self, recovery_window_hours: float = 3.0):
        self.recovery_window_hours = recovery_window_hours

    def _score_backup(
        self,
        backup: BackupRide,
        booking: CancelledBooking,
        now: datetime,
        urgency_bonus: float = 0.0,
    ) -> Optional[RecoveryCandidate]:
        """Score one backup ride for one affected passenger."""

        # Hard constraint: seats
        if backup.available_seats < booking.seats_booked:
            return None

        # Hard constraint: within recovery window
        backup_ts = backup.departure_time
        if backup_ts.tzinfo is None:
            backup_ts = backup_ts.replace(tzinfo=timezone.utc)
        if backup_ts <= now:
            return None
        orig_ts = booking.original_departure
        if orig_ts.tzinfo is None:
            orig_ts = orig_ts.replace(tzinfo=timezone.utc)
        window_diff_hours = abs((backup_ts - orig_ts).total_seconds()) / 3600.0
        if window_diff_hours > self.recovery_window_hours:
            return None

        # Score each dimension
        prox_score = _score_proximity(backup, booking)
        time_score, time_diff_mins = _score_time_urgency(backup, booking, now, self.recovery_window_hours)
        rel_score = _score_reliability(backup)
        price_score, price_diff = _score_price(backup, booking)
        detour_est = _estimate_detour(backup, booking)

        w = self.WEIGHTS
        composite = (
            w["proximity"] * prox_score
            + w["time"] * time_score
            + w["reliability"] * rel_score
            + w["price"] * price_score
            + w["urgency"] * urgency_bonus
        )
        composite = round(min(1.0, max(0.0, composite)), 4)

        shap = {
            "proximity_score": round(w["proximity"] * prox_score, 4),
            "time_score": round(w["time"] * time_score, 4),
            "reliability_score": round(w["reliability"] * rel_score, 4),
            "price_score": round(w["price"] * price_score, 4),
            "urgency_bonus": round(w["urgency"] * urgency_bonus, 4),
        }

        # Build reason
        top_factor = max(shap.items(), key=lambda x: x[1])
        price_msg = (
            f"₹{abs(price_diff):.0f} {'cheaper' if price_diff < 0 else 'more expensive'}"
            if abs(price_diff) > 10 else "similar price"
        )
        reason = (
            f"Recovery match: {composite:.0%} score. "
            f"Top factor: {top_factor[0].replace('_', ' ')}. "
            f"Departs in ~{int(time_diff_mins)} min from original. "
            f"Price: {price_msg}."
        )

        return RecoveryCandidate(
            booking_id=booking.booking_id,
            passenger_id=booking.passenger_id,
            backup_ride_id=backup.ride_id,
            backup_driver_id=backup.driver_id,
            recovery_score=composite,
            estimated_detour_mins=detour_est,
            price_difference=price_diff,
            time_difference_mins=time_diff_mins,
            match_score=prox_score,
            urgency_bonus=urgency_bonus,
            shap_contributions=shap,
            reason=reason,
            is_simulation=True,
        )

    def find_recovery(
        self,
        affected_bookings: List[CancelledBooking],
        backup_rides: List[BackupRide],
        now: Optional[datetime] = None,
        original_ride_id: Optional[UUID] = None,
        original_driver_id: Optional[UUID] = None,
        cancellation_id: Optional[UUID] = None,
        experiment_id: Optional[str] = None,
        top_k: int = 3,
    ) -> RecoveryPlan:
        """
        Find recovery options for all affected passengers.

        Args:
            affected_bookings: All confirmed bookings on the cancelled ride.
            backup_rides: Candidate rides to use as backup.
            top_k: Maximum number of ranked alternatives to return per passenger.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Filter backup_rides to exclude the original ride's driver
        # (avoid assigning back to a driver who just cancelled)
        eligible_backups = [
            b for b in backup_rides
            if original_driver_id is None or b.driver_id != original_driver_id
        ]

        recovery_plans: List[List[RecoveryCandidate]] = []
        fully_recovered = 0
        partially_recovered = 0
        unrecoverable = 0

        for booking in affected_bookings:
            candidates: List[RecoveryCandidate] = []

            for backup in eligible_backups:
                # Pre-compute urgency: if few backups available, boost score
                # (passenger needs help more urgently)
                n_eligible = sum(
                    1 for b in eligible_backups
                    if b.available_seats >= booking.seats_booked
                )
                urgency = max(0.0, 1.0 - (n_eligible / max(len(eligible_backups), 1)))

                candidate = self._score_backup(backup, booking, now, urgency)
                if candidate is not None:
                    candidates.append(candidate)

            # Sort descending by recovery score, take top_k
            candidates.sort(key=lambda c: c.recovery_score, reverse=True)
            top_candidates = candidates[:top_k]
            recovery_plans.append(top_candidates)

            if len(top_candidates) == 0:
                unrecoverable += 1
            elif top_candidates[0].recovery_score >= 0.60:
                fully_recovered += 1
            else:
                partially_recovered += 1

        n = max(len(affected_bookings), 1)
        recovery_rate = round(fully_recovered / n, 4)

        logger.info(
            "RecoveryMatch: affected=%d, recovered=%d, partial=%d, unrecoverable=%d, rate=%.1f%%",
            len(affected_bookings), fully_recovered, partially_recovered,
            unrecoverable, recovery_rate * 100
        )

        return RecoveryPlan(
            cancellation_id=cancellation_id,
            original_ride_id=original_ride_id or UUID(int=0),
            original_driver_id=original_driver_id or UUID(int=0),
            affected_passengers=len(affected_bookings),
            recovery_plans=recovery_plans,
            fully_recovered=fully_recovered,
            partially_recovered=partially_recovered,
            unrecoverable=unrecoverable,
            recovery_rate=recovery_rate,
            algorithm="B6_RECOVERYMATCH",
            is_simulation=True,
            experiment_id=experiment_id,
        )


# ─────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────
_recovery_engine: Optional[RecoveryMatchEngine] = None


def get_recovery_engine(window_hours: float = 3.0) -> RecoveryMatchEngine:
    global _recovery_engine
    if _recovery_engine is None:
        _recovery_engine = RecoveryMatchEngine(recovery_window_hours=window_hours)
        logger.info("RecoveryMatchEngine initialised: window=%.1fh", window_hours)
    return _recovery_engine
