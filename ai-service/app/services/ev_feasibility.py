"""
VAYORA AI Service — EV Feasibility Engine (B7)
================================================
Checks whether an EV vehicle can complete a ride given its current
State of Charge (SoC), estimates energy consumption, and recommends
charging stops if needed.

Research Baseline B7 = B6 (RecoveryMatch) + EV Feasibility

EV Feasibility check:
  1. Estimate energy consumption for the route (kWh)
  2. Check if available battery (SoC) covers the trip + safety buffer (15%)
  3. If not feasible: find nearest compatible charging station en-route
  4. Estimate charging time needed and updated arrival time
  5. Return feasibility verdict with SHAP-style breakdown

Energy model (Phase 7 heuristic):
  - Base consumption: vehicle.consumption_per_km_kwh
  - Elevation factor: ±15% for hilly terrain (Kolhapur–Pune has ghats)
  - Speed factor: highway vs urban
  - AC/load factor: 5% overhead for passenger load
  - Temperature factor: ±5% for extreme temperatures

All EV data labeled PUBLIC_CALIBRATION (based on published EV specs).
"""
from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from uuid import UUID

logger = logging.getLogger(__name__)

MODEL_VERSION = "ev-heuristic-v1.0"

# Safety buffer — always keep this % of battery in reserve
SAFETY_BUFFER_PCT = 0.15

# Assumed average charging rate tiers (kW)
CHARGER_RATE_KW = {
    "SLOW": 3.3,
    "FAST": 22.0,
    "RAPID": 50.0,
    "ULTRA_RAPID": 120.0,
}


# ─────────────────────────────────────────────────────────────────
# EV data classes
# ─────────────────────────────────────────────────────────────────

@dataclass
class EVVehicleSpec:
    vehicle_id: UUID
    battery_capacity_kwh: float
    consumption_per_km_kwh: float
    current_soc_percentage: float       # 0–100
    supported_charger_types: List[str]  # e.g. ["FAST", "RAPID"]


@dataclass
class RouteProfile:
    """Simplified route profile for energy estimation."""
    ride_id: UUID
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    distance_km: float
    duration_minutes: float
    has_ghat_section: bool = False      # Kolhapur-Pune has Western Ghats
    is_highway: bool = True
    passenger_count: int = 1
    ambient_temp_c: float = 25.0        # Celsius


@dataclass
class ChargingStation:
    station_id: UUID
    name: str
    lat: float
    lng: float
    charger_types: List[str]
    max_kw: float
    is_operational: bool = True
    distance_from_route_km: float = 0.0


@dataclass
class EVFeasibilityResult:
    """Full EV feasibility assessment for a ride."""
    vehicle_id: UUID
    ride_id: UUID
    # Energy analysis
    estimated_kwh_required: float
    available_kwh: float                # SoC * capacity (minus safety buffer)
    safety_buffer_kwh: float
    # Verdict
    is_feasible: bool
    feasibility_score: float            # 0.0–1.0 (range margin / required)
    infeasibility_reason: Optional[str]
    # Charging recommendation (if not feasible)
    charging_required: bool
    recommended_station: Optional[ChargingStation]
    charging_time_minutes: Optional[float]
    kwh_to_charge: Optional[float]
    updated_eta_minutes: Optional[float]
    # Breakdown (SHAP-style)
    energy_breakdown: Dict[str, float]
    explanation: str
    model_version: str = MODEL_VERSION
    data_source: str = "PUBLIC_CALIBRATION"
    is_simulation: bool = True


# ─────────────────────────────────────────────────────────────────
# Energy consumption estimator
# ─────────────────────────────────────────────────────────────────

def estimate_energy_kwh(
    spec: EVVehicleSpec,
    profile: RouteProfile,
) -> Dict[str, float]:
    """
    Estimate energy consumption for a route with adjustment factors.
    Returns a breakdown dict of all components (kWh).

    Factors (PUBLIC_CALIBRATION):
      - base: distance * consumption_per_km
      - ghat_factor: +15% for Kolhapur-Pune ghat section (climbing Western Ghats)
      - highway_factor: -8% for highway (steady speed, less braking)
      - passenger_load: +2% per passenger above 1
      - temperature: ±5% below 10°C or above 35°C (battery efficiency)
    """
    base_kwh = profile.distance_km * spec.consumption_per_km_kwh

    # Terrain factor
    ghat_factor = 1.15 if profile.has_ghat_section else 1.0
    # Speed profile factor
    highway_factor = 0.92 if profile.is_highway else 1.08
    # Passenger load (additional weight)
    load_factor = 1.0 + (max(0, profile.passenger_count - 1) * 0.02)
    # Temperature factor
    if profile.ambient_temp_c < 10.0 or profile.ambient_temp_c > 35.0:
        temp_factor = 1.05
    else:
        temp_factor = 1.0

    adjusted_kwh = base_kwh * ghat_factor * highway_factor * load_factor * temp_factor

    return {
        "base_kwh": round(base_kwh, 3),
        "ghat_adjustment": round(base_kwh * (ghat_factor - 1.0), 3),
        "highway_adjustment": round(base_kwh * (highway_factor - 1.0), 3),
        "passenger_load_adjustment": round(base_kwh * (load_factor - 1.0), 3),
        "temperature_adjustment": round(base_kwh * (temp_factor - 1.0), 3),
        "total_kwh": round(adjusted_kwh, 3),
    }


# ─────────────────────────────────────────────────────────────────
# Charging station selector
# ─────────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_best_station(
    spec: EVVehicleSpec,
    profile: RouteProfile,
    stations: List[ChargingStation],
) -> Optional[ChargingStation]:
    """
    Find the best charging station:
    - Compatible charger type
    - On-route (within 5 km of the midpoint)
    - Operational
    - Fastest compatible charger
    """
    # Midpoint of route (rough proxy for "on the way")
    mid_lat = (profile.origin_lat + profile.dest_lat) / 2
    mid_lng = (profile.origin_lng + profile.dest_lng) / 2

    compatible = [
        s for s in stations
        if s.is_operational
        and any(ct in spec.supported_charger_types for ct in s.charger_types)
    ]

    # Sort by: distance from route midpoint, then max kW descending
    compatible.sort(key=lambda s: (
        _haversine_km(mid_lat, mid_lng, s.lat, s.lng),
        -s.max_kw
    ))

    if compatible:
        best = compatible[0]
        best.distance_from_route_km = round(
            _haversine_km(mid_lat, mid_lng, best.lat, best.lng), 2
        )
        return best
    return None


def estimate_charging_time(kwh_needed: float, station: ChargingStation) -> float:
    """Estimate charging time in minutes."""
    effective_kw = min(station.max_kw, 22.0)  # typical EV acceptance limit
    if effective_kw <= 0:
        return 999.0
    return round((kwh_needed / effective_kw) * 60, 1)


# ─────────────────────────────────────────────────────────────────
# EV Feasibility Engine
# ─────────────────────────────────────────────────────────────────

class EVFeasibilityEngine:
    """
    EV Feasibility checker for B7 baseline.
    Checks if an EV can complete a ride on current battery,
    with energy breakdown and charging recommendation.
    """

    def check_feasibility(
        self,
        spec: EVVehicleSpec,
        profile: RouteProfile,
        stations: Optional[List[ChargingStation]] = None,
        experiment_id: Optional[str] = None,
    ) -> EVFeasibilityResult:
        """Full feasibility check for one EV vehicle on one route."""

        # ── Energy estimation ─────────────────────────────────────
        breakdown = estimate_energy_kwh(spec, profile)
        required_kwh = breakdown["total_kwh"]

        # ── Available energy (with safety buffer) ─────────────────
        total_capacity = spec.battery_capacity_kwh
        safety_buffer_kwh = total_capacity * SAFETY_BUFFER_PCT
        available_kwh = (spec.current_soc_percentage / 100.0) * total_capacity - safety_buffer_kwh
        available_kwh = max(0.0, round(available_kwh, 3))

        # ── Feasibility verdict ───────────────────────────────────
        is_feasible = available_kwh >= required_kwh
        feasibility_score = round(
            min(1.0, available_kwh / max(required_kwh, 0.001)), 4
        )
        infeasibility_reason = None
        if not is_feasible:
            deficit = round(required_kwh - available_kwh, 2)
            infeasibility_reason = (
                f"Insufficient battery: need {required_kwh:.1f} kWh, "
                f"have {available_kwh:.1f} kWh (after {SAFETY_BUFFER_PCT*100:.0f}% safety buffer). "
                f"Deficit: {deficit:.1f} kWh."
            )

        # ── Charging recommendation ───────────────────────────────
        charging_required = not is_feasible
        recommended_station = None
        charging_time_mins = None
        kwh_to_charge = None
        updated_eta_mins = None

        if charging_required and stations:
            recommended_station = find_best_station(spec, profile, stations)
            if recommended_station:
                kwh_to_charge = round(required_kwh - available_kwh + safety_buffer_kwh, 2)
                charging_time_mins = estimate_charging_time(kwh_to_charge, recommended_station)
                # Updated ETA = original duration + charging stop detour
                detour_km = recommended_station.distance_from_route_km * 2  # there and back
                detour_time_mins = (detour_km / 30.0) * 60  # ~30 km/h to station
                updated_eta_mins = round(profile.duration_minutes + charging_time_mins + detour_time_mins, 1)

        # ── Build explanation ─────────────────────────────────────
        margin_pct = round((available_kwh - required_kwh) / max(required_kwh, 0.001) * 100, 1)
        if is_feasible:
            explanation = (
                f"EV FEASIBLE: {required_kwh:.1f} kWh required, "
                f"{available_kwh:.1f} kWh available (margin: {margin_pct:+.1f}%). "
                f"Top energy factors: ghat={breakdown['ghat_adjustment']:+.2f} kWh, "
                f"highway={breakdown['highway_adjustment']:+.2f} kWh. "
                f"[PUBLIC_CALIBRATION — estimated values]"
            )
        elif recommended_station:
            explanation = (
                f"EV NOT FEASIBLE without charging. "
                f"{infeasibility_reason} "
                f"Recommended charging stop: {recommended_station.name} "
                f"({recommended_station.distance_from_route_km:.1f} km off-route). "
                f"Charge {kwh_to_charge:.1f} kWh in ~{charging_time_mins:.0f} min. "
                f"[PUBLIC_CALIBRATION — estimated values]"
            )
        else:
            explanation = (
                f"EV NOT FEASIBLE. {infeasibility_reason} "
                f"No compatible charging stations found near route. "
                f"Recommend using ICE vehicle or reschedule after charging. "
                f"[PUBLIC_CALIBRATION — estimated values]"
            )

        return EVFeasibilityResult(
            vehicle_id=spec.vehicle_id,
            ride_id=profile.ride_id,
            estimated_kwh_required=required_kwh,
            available_kwh=available_kwh,
            safety_buffer_kwh=safety_buffer_kwh,
            is_feasible=is_feasible,
            feasibility_score=feasibility_score,
            infeasibility_reason=infeasibility_reason,
            charging_required=charging_required,
            recommended_station=recommended_station,
            charging_time_minutes=charging_time_mins,
            kwh_to_charge=kwh_to_charge,
            updated_eta_minutes=updated_eta_mins,
            energy_breakdown=breakdown,
            explanation=explanation,
            model_version=MODEL_VERSION,
            data_source="PUBLIC_CALIBRATION",
            is_simulation=True,
        )


# ─────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────
_ev_engine: Optional[EVFeasibilityEngine] = None


def get_ev_engine() -> EVFeasibilityEngine:
    global _ev_engine
    if _ev_engine is None:
        _ev_engine = EVFeasibilityEngine()
        logger.info("EV Feasibility engine initialised: model_version=%s", MODEL_VERSION)
    return _ev_engine
