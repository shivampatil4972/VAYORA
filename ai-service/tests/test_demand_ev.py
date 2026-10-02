"""
Unit tests for VAYORA DemandAI (B5) and EV Feasibility (B7).
Pure Python — no DB / network required.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.services.demand import (
    DemandAIEngine, HistoricalRecord, lat_lng_to_zone,
    compute_gap_score, baseline_demand
)
from app.services.ev_feasibility import (
    EVFeasibilityEngine, EVVehicleSpec, RouteProfile, ChargingStation,
    estimate_energy_kwh, find_best_station, estimate_charging_time
)


# ─────────────────────────────────────────────
# DemandAI (B5) tests
# ─────────────────────────────────────────────

def make_historical_record(searches=10, unfulfilled=3, hour=8, dow=0):
    return HistoricalRecord(
        zone_id="16.7_74.2",
        hour_of_day=hour,
        day_of_week=dow,
        total_searches=searches,
        fulfilled_searches=searches - unfulfilled,
        unfulfilled_searches=unfulfilled,
        total_rides_offered=5,
    )

def test_lat_lng_to_zone():
    assert lat_lng_to_zone(16.705, 74.243, precision=1) == "16.7_74.2"
    assert lat_lng_to_zone(16.706, 74.243, precision=2) == "16.71_74.24"

def test_gap_score_scaling():
    # Gap score is unfulfilled ratio * volume weight
    rec_low_vol = make_historical_record(searches=10, unfulfilled=10) # 100% unfulfilled
    rec_high_vol = make_historical_record(searches=100, unfulfilled=100) # 100% unfulfilled

    gap_low = compute_gap_score(rec_low_vol)
    gap_high = compute_gap_score(rec_high_vol)

    assert gap_low < 1.0  # Amplified down because volume < 50
    assert gap_high == 1.0 # Max severity

def test_demand_prediction_ranking():
    engine = DemandAIEngine()
    records = [
        make_historical_record(searches=50, unfulfilled=0),   # 0 gap
        make_historical_record(searches=50, unfulfilled=50),  # Max gap
    ]
    # To avoid matching zone_id which causes overwrite in dicts (if used), change zone_id
    records[0].zone_id = "1.0_1.0"
    records[1].zone_id = "2.0_2.0"
    
    preds = engine.predict_zone_demand(records, 8, 1)
    
    # Should be sorted by gap_score descending
    assert len(preds) == 2
    assert preds[0].zone_id == "2.0_2.0"
    assert preds[0].gap_score > preds[1].gap_score

def test_nudge_generation():
    engine = DemandAIEngine()
    records = [
        make_historical_record(searches=100, unfulfilled=80),  # High demand gap
    ]
    records[0].zone_id = "16.7_74.2"
    preds = engine.predict_zone_demand(records, 8, 1)
    
    # Driver is at 16.8, 74.2 (close to 16.7, 74.2)
    nudges = engine.generate_nudges(
        preds, driver_id=uuid4(), driver_lat=16.8, driver_lng=74.2, max_nudge_km=30.0
    )
    
    assert len(nudges) == 1
    assert nudges[0].target_zone == "16.7_74.2"
    assert nudges[0].urgency == "HIGH"
    assert nudges[0].is_simulation is True

def test_heatmap_generation():
    engine = DemandAIEngine()
    records = [
        make_historical_record(searches=10, unfulfilled=0),
        make_historical_record(searches=100, unfulfilled=80),
    ]
    records[0].zone_id = "1.0_1.0"
    records[1].zone_id = "2.0_2.0"
    preds = engine.predict_zone_demand(records, 8, 1)
    
    heatmap = engine.generate_heatmap(preds)
    
    assert len(heatmap.cells) == 2
    high_demand_cell = next(c for c in heatmap.cells if c.gap_score > 0.5)
    assert high_demand_cell.label == "HIGH DEMAND GAP"


# ─────────────────────────────────────────────
# EV Feasibility (B7) tests
# ─────────────────────────────────────────────

def make_ev_spec(capacity=40.0, consumption=0.15, soc=100.0) -> EVVehicleSpec:
    return EVVehicleSpec(
        vehicle_id=uuid4(),
        battery_capacity_kwh=capacity,
        consumption_per_km_kwh=consumption,
        current_soc_percentage=soc,
        supported_charger_types=["FAST", "RAPID"]
    )

def make_route(distance=200.0, ghat=False, highway=True, temp=25.0) -> RouteProfile:
    return RouteProfile(
        ride_id=uuid4(),
        origin_lat=16.70, origin_lng=74.24,
        dest_lat=18.52, dest_lng=73.85,
        distance_km=distance,
        duration_minutes=distance / 60.0 * 60,
        has_ghat_section=ghat,
        is_highway=highway,
        ambient_temp_c=temp,
    )

def make_station(lat=17.5, lng=74.0, max_kw=50.0, types=None) -> ChargingStation:
    if types is None:
        types = ["FAST", "RAPID"]
    return ChargingStation(
        station_id=uuid4(),
        name="Test Station",
        lat=lat, lng=lng,
        charger_types=types,
        max_kw=max_kw,
    )

def test_energy_estimation_factors():
    spec = make_ev_spec(consumption=0.15)
    
    # Base: 100km * 0.15 = 15 kWh
    # Ghat: +15%
    # Highway: -8%
    # Load (1 pax): 0%
    # Temp (25C): 0%
    profile = make_route(distance=100.0, ghat=True, highway=True)
    breakdown = estimate_energy_kwh(spec, profile)
    
    assert breakdown["base_kwh"] == 15.0
    assert breakdown["ghat_adjustment"] > 0
    assert breakdown["highway_adjustment"] < 0
    assert breakdown["temperature_adjustment"] == 0.0

def test_ev_feasible_trip():
    engine = EVFeasibilityEngine()
    spec = make_ev_spec(capacity=50.0, soc=100.0, consumption=0.15) # 50kWh available, 100%
    profile = make_route(distance=100.0) # ~15kWh required
    
    res = engine.check_feasibility(spec, profile)
    
    assert res.is_feasible is True
    assert res.charging_required is False
    assert res.recommended_station is None

def test_ev_infeasible_trip_needs_charge():
    engine = EVFeasibilityEngine()
    # 50kWh capacity, 20% soc = 10kWh available. Safety buffer = 15% (7.5kWh). Usable = 2.5kWh.
    spec = make_ev_spec(capacity=50.0, soc=20.0, consumption=0.15) 
    profile = make_route(distance=200.0) # ~30kWh required
    
    station = make_station()
    res = engine.check_feasibility(spec, profile, [station])
    
    assert res.is_feasible is False
    assert res.charging_required is True
    assert res.recommended_station is not None
    assert res.kwh_to_charge > 0

def test_find_best_station_compatibility():
    spec = make_ev_spec(capacity=50.0)
    spec.supported_charger_types = ["SLOW"]
    
    profile = make_route()
    
    s1 = make_station(max_kw=50.0, types=["RAPID"]) # Incompatible
    s2 = make_station(max_kw=3.3, types=["SLOW"])   # Compatible
    
    best = find_best_station(spec, profile, [s1, s2])
    
    assert best is not None
    assert best.max_kw == 3.3

def test_find_best_station_distance():
    spec = make_ev_spec()
    profile = make_route()
    
    # Midpoint of 16.7/74.24 to 18.52/73.85 is roughly 17.6, 74.04
    s_far = make_station(lat=10.0, lng=10.0)
    s_near = make_station(lat=17.6, lng=74.04)
    
    best = find_best_station(spec, profile, [s_far, s_near])
    assert best is not None
    assert best.station_id == s_near.station_id
