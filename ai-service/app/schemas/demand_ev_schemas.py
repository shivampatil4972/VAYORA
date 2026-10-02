"""
VAYORA AI Service — DemandAI & EV Pydantic Schemas (B5, B7)
"""
from __future__ import annotations

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# B5 — DemandAI Schemas
# ─────────────────────────────────────────────

class HistoricalRecordSchema(BaseModel):
    """Aggregated search stats per zone (built from ride_requests table)."""
    zone_id: str
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    total_searches: int = Field(..., ge=0)
    fulfilled_searches: int = Field(..., ge=0)
    unfulfilled_searches: int = Field(..., ge=0)
    total_rides_offered: int = Field(..., ge=0)


class DemandPredictRequest(BaseModel):
    """
    B5: DemandAI prediction request.
    Provide historical records for zones, get demand predictions + gap scores back.
    """
    records: List[HistoricalRecordSchema] = Field(..., min_length=1)
    target_hour: int = Field(..., ge=0, le=23)
    target_day_of_week: int = Field(..., ge=0, le=6)
    experiment_id: Optional[str] = None


class DemandPredictionSchema(BaseModel):
    zone_id: str
    center_lat: float
    center_lng: float
    prediction_hour: int
    day_of_week: int
    expected_demand: float
    expected_supply: float
    gap_score: float
    fulfillment_rate: float
    confidence: str
    data_source: str
    model_version: str


class DemandPredictResponse(BaseModel):
    predictions: List[DemandPredictionSchema]
    total_zones: int
    high_gap_zones: int     # zones with gap_score > 0.5
    is_simulation: bool = True
    experiment_id: Optional[str] = None
    generated_at: datetime


class NudgeRequest(BaseModel):
    """Generate repositioning nudges for a specific driver."""
    driver_id: UUID
    driver_lat: float
    driver_lng: float
    predictions: List[DemandPredictionSchema]
    max_nudge_km: float = Field(30.0, ge=1.0, le=100.0)
    top_n: int = Field(3, ge=1, le=10)


class DriverNudgeSchema(BaseModel):
    driver_id: UUID
    current_zone: str
    target_zone: str
    target_lat: float
    target_lng: float
    distance_km: float
    demand_gap_score: float
    expected_demand: float
    nudge_message: str
    urgency: str
    is_simulation: bool = True


class NudgeResponse(BaseModel):
    driver_id: UUID
    nudges: List[DriverNudgeSchema]
    is_simulation: bool = True


class HeatmapCellSchema(BaseModel):
    lat: float
    lng: float
    demand_score: float
    gap_score: float
    label: str


class HeatmapResponse(BaseModel):
    cells: List[HeatmapCellSchema]
    generated_at: datetime
    hour: int
    day_of_week: int
    is_simulation: bool = True


# ─────────────────────────────────────────────
# B7 — EV Feasibility Schemas
# ─────────────────────────────────────────────

class EVVehicleSpecSchema(BaseModel):
    vehicle_id: UUID
    battery_capacity_kwh: float = Field(..., gt=0)
    consumption_per_km_kwh: float = Field(..., gt=0)
    current_soc_percentage: float = Field(..., ge=0, le=100)
    supported_charger_types: List[str] = Field(default_factory=list)


class RouteProfileSchema(BaseModel):
    ride_id: UUID
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    distance_km: float = Field(..., gt=0)
    duration_minutes: float = Field(..., gt=0)
    has_ghat_section: bool = False
    is_highway: bool = True
    passenger_count: int = Field(1, ge=1, le=8)
    ambient_temp_c: float = 25.0


class ChargingStationSchema(BaseModel):
    station_id: UUID
    name: str
    lat: float
    lng: float
    charger_types: List[str]
    max_kw: float
    is_operational: bool = True
    distance_from_route_km: float = 0.0


class EVFeasibilityRequest(BaseModel):
    """
    B7: EV feasibility check request.
    Spring Boot sends this when a driver with an EV creates a ride.
    """
    ev_spec: EVVehicleSpecSchema
    route: RouteProfileSchema
    nearby_stations: List[ChargingStationSchema] = Field(default_factory=list)
    experiment_id: Optional[str] = None


class EVFeasibilityResponse(BaseModel):
    vehicle_id: UUID
    ride_id: UUID
    estimated_kwh_required: float
    available_kwh: float
    safety_buffer_kwh: float
    is_feasible: bool
    feasibility_score: float
    infeasibility_reason: Optional[str] = None
    charging_required: bool
    recommended_station: Optional[ChargingStationSchema] = None
    charging_time_minutes: Optional[float] = None
    kwh_to_charge: Optional[float] = None
    updated_eta_minutes: Optional[float] = None
    energy_breakdown: Dict[str, float]
    explanation: str
    model_version: str
    data_source: str
    is_simulation: bool = True
    experiment_id: Optional[str] = None
