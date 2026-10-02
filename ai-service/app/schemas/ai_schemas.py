"""
VAYORA AI Service — Pydantic Schemas
SmartMatch request/response models.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


# ─────────────────────────────────────────────
# Shared geo primitives
# ─────────────────────────────────────────────

class GeoPoint(BaseModel):
    """WGS-84 coordinate pair."""
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude")


# ─────────────────────────────────────────────
# SmartMatch schemas
# ─────────────────────────────────────────────

class RideCandidate(BaseModel):
    """A ride candidate returned by the Spring Boot B0 search, to be re-ranked by SmartMatch."""
    ride_id: UUID
    driver_id: UUID
    origin: GeoPoint
    destination: GeoPoint
    departure_time: datetime
    available_seats: int
    price_per_seat: float
    max_detour_minutes: int = 20
    # Driver reliability features (fetched from DB or passed in)
    driver_completed_rides: int = 0
    driver_cancellations: int = 0
    driver_avg_rating: Optional[float] = None
    journey_confidence_score: Optional[float] = None


class PassengerPreferences(BaseModel):
    """Passenger-side preferences for two-sided matching."""
    wheelchair_required: bool = False
    allows_pets: bool = False
    preferred_max_price: Optional[float] = None
    preferred_max_detour: int = 30  # minutes


class SmartMatchRequest(BaseModel):
    """
    B2: Two-sided matching request.
    Takes the B0 candidate list and passenger context, returns a scored + ranked list.
    """
    passenger_id: UUID
    search_origin: GeoPoint
    search_destination: GeoPoint
    requested_departure: datetime
    seats_needed: int = Field(..., ge=1, le=8)
    preferences: PassengerPreferences = PassengerPreferences()
    candidates: List[RideCandidate] = Field(..., min_length=1)
    experiment_id: Optional[str] = None  # 'B0', 'B1', 'B2', etc.


class MatchScore(BaseModel):
    """Scored match result with SHAP-style explanations."""
    ride_id: UUID
    driver_id: UUID
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Overall match score 0–1")
    # Sub-scores (for explainability)
    geo_score: float
    time_score: float
    price_score: float
    reliability_score: float
    preference_score: float
    # SHAP-style feature contributions (Explainable AI)
    shap_contributions: Dict[str, float]
    # Human-readable reasons
    match_reason: str
    # Original candidate data
    departure_time: datetime
    price_per_seat: float
    available_seats: int


class SmartMatchResponse(BaseModel):
    """Ranked and scored ride matches returned to the passenger."""
    passenger_id: UUID
    total_candidates: int
    ranked_matches: List[MatchScore]
    algorithm: str  # 'B0_FILTER', 'B1_RULE_BASED', 'B2_SMARTMATCH'
    experiment_id: Optional[str]
    processed_at: datetime


# ─────────────────────────────────────────────
# ReliabilityAI schemas
# ─────────────────────────────────────────────

class ReliabilityFeatures(BaseModel):
    """
    Features used by ReliabilityAI to predict P(cancel) for a driver.
    All features are factual metrics — no character inferences (AI Ethics).
    """
    driver_id: UUID
    ride_id: UUID
    completed_rides: int = 0
    cancellations: int = 0
    avg_late_start_minutes: float = 0.0
    no_show_count: int = 0
    avg_rating: Optional[float] = None
    days_since_last_ride: Optional[int] = None
    distance_km: float = 0.0
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    # Ride-level factors
    seats_offered: int = 1
    price_per_seat: float = 0.0
    max_detour_minutes: int = 20
    experiment_id: Optional[str] = None


class ReliabilityPrediction(BaseModel):
    """
    ReliabilityAI output: P_CANCEL, confidence band, and SHAP explanation.
    Note: This is a PREDICTION, not a guarantee (AI Ethics).
    """
    driver_id: UUID
    ride_id: UUID
    p_cancel: float = Field(..., ge=0.0, le=1.0, description="Probability driver cancels")
    p_complete: float = Field(..., ge=0.0, le=1.0)
    confidence: str  # 'LOW', 'MEDIUM', 'HIGH' based on data volume
    reliability_band: str  # 'VERY_RELIABLE', 'RELIABLE', 'MODERATE', 'RISKY'
    shap_contributions: Dict[str, float]
    explanation: str  # Human-readable
    model_version: str
    is_simulation: bool = True  # Labeled per research ethics
    experiment_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_probabilities(self) -> "ReliabilityPrediction":
        # Ensure p_cancel + p_complete ≈ 1
        if abs((self.p_cancel + self.p_complete) - 1.0) > 0.01:
            self.p_complete = round(1.0 - self.p_cancel, 4)
        return self


# ─────────────────────────────────────────────
# ML Prediction persistence schema
# ─────────────────────────────────────────────

class MLPredictionRecord(BaseModel):
    """Schema for storing a prediction in the ml_predictions table."""
    model_name: str
    model_version: str
    target_entity_id: UUID
    target_entity_type: str  # 'RIDE', 'BOOKING', 'DRIVER'
    prediction_type: str     # 'P_CANCEL', 'P_BOOK', 'MATCH_SCORE'
    prediction_value: float
    features_json: Optional[Dict[str, Any]] = None
    shap_values: Optional[Dict[str, float]] = None
    experiment_id: Optional[str] = None
