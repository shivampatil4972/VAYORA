"""
Unit tests for VAYORA Optimizer (B3) and RecoveryMatch (B6).
Pure Python — no DB / network required.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.services.optimizer import (
    OptRide, OptPassenger, RideOptimizer, greedy_assign,
    is_feasible, is_time_compatible, is_seat_compatible, ORTOOLS_AVAILABLE,
)
from app.services.recovery import (
    RecoveryMatchEngine, CancelledBooking, BackupRide,
    _haversine_km, _score_proximity, _score_reliability,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def future(hours: float = 2.0) -> datetime:
    return now_utc() + timedelta(hours=hours)


def make_ride(seats: int = 3, dep_offset_hours: float = 2.0, price: float = 350.0) -> OptRide:
    return OptRide(
        ride_id=uuid4(),
        driver_id=uuid4(),
        available_seats=seats,
        departure_time=future(dep_offset_hours),
        max_detour_minutes=20,
        price_per_seat=price,
        origin_lat=16.705,
        origin_lng=74.243,
        dest_lat=18.520,
        dest_lng=73.857,
    )


def make_passenger(
    seats: int = 1,
    dep_offset_hours: float = 2.0,
    max_price: float = None,
    match_scores: dict = None,
) -> OptPassenger:
    return OptPassenger(
        passenger_id=uuid4(),
        request_id=uuid4(),
        seats_needed=seats,
        requested_departure=future(dep_offset_hours),
        origin_lat=16.705,
        origin_lng=74.243,
        dest_lat=18.520,
        dest_lng=73.857,
        max_price=max_price,
        match_scores=match_scores or {},
    )


def make_booking(
    seats: int = 1,
    dep_offset_hours: float = 2.0,
    price_paid: float = 350.0,
) -> CancelledBooking:
    return CancelledBooking(
        booking_id=uuid4(),
        passenger_id=uuid4(),
        original_ride_id=uuid4(),
        original_driver_id=uuid4(),
        seats_booked=seats,
        original_departure=future(dep_offset_hours),
        pickup_lat=16.705,
        pickup_lng=74.243,
        dropoff_lat=18.520,
        dropoff_lng=73.857,
        total_price_paid=price_paid,
    )


def make_backup(
    seats: int = 3,
    dep_offset_hours: float = 2.5,
    price: float = 380.0,
    driver_id=None,
) -> BackupRide:
    return BackupRide(
        ride_id=uuid4(),
        driver_id=driver_id or uuid4(),
        available_seats=seats,
        departure_time=future(dep_offset_hours),
        price_per_seat=price,
        max_detour_minutes=20,
        origin_lat=16.72,
        origin_lng=74.25,
        dest_lat=18.52,
        dest_lng=73.86,
        driver_completed_rides=20,
        driver_cancellations=1,
        driver_avg_rating=4.3,
    )


# ─────────────────────────────────────────────
# Optimizer feasibility tests
# ─────────────────────────────────────────────

def test_feasibility_compatible():
    ride = make_ride(seats=3)
    passenger = make_passenger(seats=1)
    assert is_feasible(ride, passenger)


def test_feasibility_seat_constraint():
    ride = make_ride(seats=1)
    passenger = make_passenger(seats=3)
    assert not is_feasible(ride, passenger)


def test_feasibility_time_constraint():
    ride = make_ride(dep_offset_hours=6.0)   # 6h away
    passenger = make_passenger(dep_offset_hours=2.0)  # wants 2h
    assert not is_time_compatible(ride, passenger, tolerance_hours=2.0)


def test_feasibility_time_within_tolerance():
    ride = make_ride(dep_offset_hours=3.5)   # 1.5h difference from passenger's 2h
    passenger = make_passenger(dep_offset_hours=2.0)
    assert is_time_compatible(ride, passenger, tolerance_hours=2.0)


def test_feasibility_price_constraint():
    ride = make_ride(price=600.0)
    passenger = make_passenger(max_price=400.0)
    assert not is_feasible(ride, passenger)


# ─────────────────────────────────────────────
# Greedy fallback tests
# ─────────────────────────────────────────────

def test_greedy_basic_assignment():
    rides = [make_ride(seats=3)]
    passengers = [make_passenger(seats=1)]
    result = greedy_assign(rides, passengers)
    assert result.total_assigned == 1
    assert result.total_unassigned == 0
    assert result.solver_status == "GREEDY_FALLBACK"


def test_greedy_seat_overflow():
    """3 passengers wanting 2 seats each, only 1 ride with 3 seats — can only assign 1."""
    ride = make_ride(seats=3)
    passengers = [make_passenger(seats=2) for _ in range(3)]
    result = greedy_assign([ride], passengers)
    assert result.total_assigned == 1
    assert result.total_unassigned == 2


def test_greedy_multiple_rides():
    """3 rides, 3 passengers — all should be assignable."""
    rides = [make_ride(seats=3) for _ in range(3)]
    passengers = [make_passenger(seats=1) for _ in range(3)]
    result = greedy_assign(rides, passengers)
    assert result.total_assigned == 3


def test_greedy_no_rides():
    """No rides available — no assignments."""
    passengers = [make_passenger(seats=1) for _ in range(3)]
    result = greedy_assign([], passengers)
    assert result.total_assigned == 0
    assert result.total_unassigned == 3


def test_greedy_prefers_higher_score():
    """Greedy should prefer the ride with the higher match score."""
    rides = [make_ride(seats=2), make_ride(seats=2)]
    p = make_passenger(seats=1, match_scores={0: 30, 1: 90})
    result = greedy_assign(rides, [p])
    assert result.total_assigned == 1
    assert result.assignments[0].ride_id == rides[1].ride_id


# ─────────────────────────────────────────────
# OR-Tools optimizer tests
# ─────────────────────────────────────────────

@pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="OR-Tools not installed")
def test_ortools_basic_assignment():
    optimizer = RideOptimizer(solver_timeout_seconds=5)
    rides = [make_ride(seats=3)]
    passengers = [make_passenger(seats=1, match_scores={0: 80})]
    result = optimizer.optimize(rides, passengers)
    assert result.total_assigned == 1
    assert result.solver_status in ("OPTIMAL", "FEASIBLE")
    assert result.is_simulation is True


@pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="OR-Tools not installed")
def test_ortools_seat_constraint():
    """Optimizer must not exceed seat capacity."""
    optimizer = RideOptimizer(solver_timeout_seconds=5)
    ride = make_ride(seats=2)
    passengers = [make_passenger(seats=1, match_scores={0: 80}) for _ in range(5)]
    result = optimizer.optimize([ride], passengers)
    assert result.total_assigned <= 2


@pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="OR-Tools not installed")
def test_ortools_maximizes_score():
    """Optimizer should pick higher-scoring assignments over lower ones."""
    optimizer = RideOptimizer(solver_timeout_seconds=5)
    rides = [make_ride(seats=1), make_ride(seats=1)]
    p1 = make_passenger(seats=1, match_scores={0: 90, 1: 10})
    p2 = make_passenger(seats=1, match_scores={0: 10, 1: 90})
    result = optimizer.optimize(rides, [p1, p2])
    # Both should be assigned (different rides), maximizing total score (90+90=180)
    assert result.total_assigned == 2
    assert result.objective_value >= 180


def test_optimizer_empty_passengers():
    optimizer = RideOptimizer()
    result = optimizer.optimize([make_ride()], [])
    assert result.total_assigned == 0
    # When OR-Tools is available → INFEASIBLE; when using greedy fallback → GREEDY_FALLBACK
    assert result.solver_status in ("INFEASIBLE", "GREEDY_FALLBACK")


# ─────────────────────────────────────────────
# RecoveryMatch tests
# ─────────────────────────────────────────────

def test_recovery_basic():
    """Single booking, one backup ride — should recover."""
    engine = RecoveryMatchEngine(recovery_window_hours=3.0)
    booking = make_booking(seats=1, dep_offset_hours=2.0)
    backup = make_backup(seats=3, dep_offset_hours=2.5)
    original_id = uuid4()
    plan = engine.find_recovery(
        affected_bookings=[booking],
        backup_rides=[backup],
        original_ride_id=original_id,
        original_driver_id=uuid4(),
    )
    assert plan.affected_passengers == 1
    assert len(plan.recovery_plans[0]) > 0
    assert plan.fully_recovered + plan.partially_recovered >= 1


def test_recovery_no_backups():
    """No backup rides → passenger is unrecoverable, but plan still returned."""
    engine = RecoveryMatchEngine()
    booking = make_booking()
    plan = engine.find_recovery(
        affected_bookings=[booking],
        backup_rides=[],
        original_ride_id=uuid4(),
        original_driver_id=uuid4(),
    )
    assert plan.unrecoverable == 1
    assert plan.recovery_rate == 0.0
    assert len(plan.recovery_plans[0]) == 0


def test_recovery_excludes_cancelled_driver():
    """Backup ride by the same driver who cancelled should be excluded."""
    engine = RecoveryMatchEngine()
    original_driver = uuid4()
    booking = make_booking()
    # Backup ride by the SAME driver
    same_driver_backup = make_backup(driver_id=original_driver)
    plan = engine.find_recovery(
        affected_bookings=[booking],
        backup_rides=[same_driver_backup],
        original_ride_id=uuid4(),
        original_driver_id=original_driver,
    )
    assert plan.unrecoverable == 1  # Excluded because same driver


def test_recovery_outside_window():
    """Backup ride outside recovery window should be excluded."""
    engine = RecoveryMatchEngine(recovery_window_hours=1.0)
    booking = make_booking(dep_offset_hours=2.0)
    backup = make_backup(dep_offset_hours=6.0)  # 4h difference — outside 1h window
    plan = engine.find_recovery(
        affected_bookings=[booking],
        backup_rides=[backup],
        original_ride_id=uuid4(),
        original_driver_id=uuid4(),
    )
    assert plan.unrecoverable == 1


def test_recovery_ranked_by_score():
    """Multiple backups should be returned ranked by recovery_score descending."""
    engine = RecoveryMatchEngine(recovery_window_hours=3.0)
    booking = make_booking(seats=1, dep_offset_hours=2.0)
    backups = [
        make_backup(seats=3, dep_offset_hours=2.1, price=350.0),  # close in time, cheap
        make_backup(seats=3, dep_offset_hours=2.5, price=600.0),  # later, expensive
    ]
    plan = engine.find_recovery(
        affected_bookings=[booking],
        backup_rides=backups,
        original_ride_id=uuid4(),
        original_driver_id=uuid4(),
    )
    candidates = plan.recovery_plans[0]
    if len(candidates) >= 2:
        assert candidates[0].recovery_score >= candidates[1].recovery_score


def test_recovery_top_k_limit():
    """Should not return more than top_k candidates per passenger."""
    engine = RecoveryMatchEngine(recovery_window_hours=3.0)
    booking = make_booking(seats=1)
    backups = [make_backup(seats=3, dep_offset_hours=2.0 + i * 0.1) for i in range(10)]
    plan = engine.find_recovery(
        affected_bookings=[booking],
        backup_rides=backups,
        original_ride_id=uuid4(),
        original_driver_id=uuid4(),
        top_k=3,
    )
    assert len(plan.recovery_plans[0]) <= 3


def test_recovery_simulation_labeled():
    """All recovery plans must be labeled as SIMULATION."""
    engine = RecoveryMatchEngine()
    booking = make_booking()
    backup = make_backup()
    plan = engine.find_recovery(
        affected_bookings=[booking],
        backup_rides=[backup],
        original_ride_id=uuid4(),
        original_driver_id=uuid4(),
    )
    assert plan.is_simulation is True
    for candidates in plan.recovery_plans:
        for c in candidates:
            assert c.is_simulation is True


def test_recovery_multiple_passengers():
    """Multiple affected passengers should each get their own plan."""
    engine = RecoveryMatchEngine(recovery_window_hours=3.0)
    bookings = [make_booking(seats=1, dep_offset_hours=2.0) for _ in range(3)]
    backup = make_backup(seats=5, dep_offset_hours=2.5)
    plan = engine.find_recovery(
        affected_bookings=bookings,
        backup_rides=[backup],
        original_ride_id=uuid4(),
        original_driver_id=uuid4(),
    )
    assert plan.affected_passengers == 3
    assert len(plan.recovery_plans) == 3


def test_recovery_rate_calculation():
    """Recovery rate = fully_recovered / affected_passengers."""
    engine = RecoveryMatchEngine(recovery_window_hours=3.0)
    bookings = [make_booking() for _ in range(4)]
    # One very good backup
    backup = make_backup(seats=10, dep_offset_hours=2.0, price=350.0)
    plan = engine.find_recovery(
        affected_bookings=bookings,
        backup_rides=[backup],
        original_ride_id=uuid4(),
        original_driver_id=uuid4(),
    )
    expected_rate = plan.fully_recovered / 4
    assert abs(plan.recovery_rate - expected_rate) < 0.01


def test_haversine_zero():
    assert _haversine_km(0, 0, 0, 0) == pytest.approx(0.0, abs=0.001)
