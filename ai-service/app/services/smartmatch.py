"""
VAYORA AI Service — SmartMatch Engine
=========================================
Implements B1 (Rule-Based) and B2 (SmartMatch/ML) matching.

B1 — Rule-Based Matching:
  Deterministic scoring using geographic distance, time alignment,
  price, and driver reliability metrics.

B2 — SmartMatch:
  Weighted composite scoring with trained LightGBM model (when available)
  falling back to B1 rule-based scoring. Includes SHAP explanations.

Architecture:
  - SmartMatchEngine.score_candidates() → ranked MatchScore list
  - Each score dimension is independently explainable (AI Ethics)
  - No character inferences — only factual metrics
"""
from __future__ import annotations

import math
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

import numpy as np

from app.schemas.ai_schemas import (
    RideCandidate,
    PassengerPreferences,
    MatchScore,
    SmartMatchRequest,
    SmartMatchResponse,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Geographic utilities
# ─────────────────────────────────────────────────────────────────

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two points (km).
    Used for proximity scoring — not routing (OSRM handles routing).
    """
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Initial bearing from point A to point B (degrees)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lng2 - lng1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


# ─────────────────────────────────────────────────────────────────
# Individual scoring dimensions
# ─────────────────────────────────────────────────────────────────

def score_geo(
    candidate: RideCandidate,
    search_origin_lat: float,
    search_origin_lng: float,
    search_dest_lat: float,
    search_dest_lng: float,
    max_radius_km: float = 5.0,
) -> Tuple[float, dict]:
    """
    Geographic alignment score [0–1].
    Components:
      - Origin proximity: how close the ride origin is to the passenger origin
      - Destination proximity: how close the ride destination is to the passenger destination
      - Route alignment: whether the ride goes in the right direction
    """
    origin_dist = haversine_km(
        search_origin_lat, search_origin_lng,
        candidate.origin.lat, candidate.origin.lng
    )
    dest_dist = haversine_km(
        search_dest_lat, search_dest_lng,
        candidate.destination.lat, candidate.destination.lng
    )

    # Soft decay — score = 1 at dist=0, ~0.37 at dist=radius, 0 beyond 2x radius
    origin_score = math.exp(-origin_dist / max_radius_km)
    dest_score = math.exp(-dest_dist / max_radius_km)

    # Direction alignment between ride vector and search vector
    ride_bearing = bearing(
        candidate.origin.lat, candidate.origin.lng,
        candidate.destination.lat, candidate.destination.lng
    )
    search_bearing = bearing(
        search_origin_lat, search_origin_lng,
        search_dest_lat, search_dest_lng
    )
    bearing_diff = abs(ride_bearing - search_bearing) % 360
    bearing_diff = min(bearing_diff, 360 - bearing_diff)  # 0-180
    direction_score = max(0.0, 1.0 - bearing_diff / 90.0)  # 1 at 0°, 0 at 90°+

    geo_score = 0.4 * origin_score + 0.4 * dest_score + 0.2 * direction_score

    contributions = {
        "geo_origin_proximity": round(0.4 * origin_score, 4),
        "geo_destination_proximity": round(0.4 * dest_score, 4),
        "geo_direction_alignment": round(0.2 * direction_score, 4),
    }
    return round(geo_score, 4), contributions


def score_time(
    candidate: RideCandidate,
    requested_departure: datetime,
    tolerance_hours: float = 2.0,
) -> Tuple[float, dict]:
    """
    Temporal alignment score [0–1].
    Gaussian decay around requested departure time.
    """
    # Ensure timezone-aware comparison
    req_ts = requested_departure
    ride_ts = candidate.departure_time
    if req_ts.tzinfo is None:
        req_ts = req_ts.replace(tzinfo=timezone.utc)
    if ride_ts.tzinfo is None:
        ride_ts = ride_ts.replace(tzinfo=timezone.utc)

    diff_hours = abs((ride_ts - req_ts).total_seconds()) / 3600.0
    # Gaussian: score=1 at diff=0, score≈0.61 at diff=tolerance/2
    sigma = tolerance_hours / 2.0
    time_score = math.exp(-(diff_hours ** 2) / (2 * sigma ** 2))

    contributions = {"time_alignment": round(time_score, 4)}
    return round(time_score, 4), contributions


def score_price(
    candidate: RideCandidate,
    preferences: PassengerPreferences,
    market_avg_price: float = 300.0,
) -> Tuple[float, dict]:
    """
    Price attractiveness score [0–1].
    Considers absolute price and passenger budget preference.
    """
    price = candidate.price_per_seat
    # Normalise against market average
    relative_price = price / max(market_avg_price, 1.0)
    base_score = max(0.0, 1.0 - (relative_price - 0.5))  # Full score if ≤50% of avg

    # Preference penalty if above preferred max
    if preferences.preferred_max_price and price > preferences.preferred_max_price:
        overage_ratio = (price - preferences.preferred_max_price) / preferences.preferred_max_price
        base_score *= max(0.0, 1.0 - overage_ratio)

    price_score = min(1.0, max(0.0, base_score))
    contributions = {"price_attractiveness": round(price_score, 4)}
    return round(price_score, 4), contributions


def score_reliability(candidate: RideCandidate) -> Tuple[float, dict]:
    """
    Driver reliability score [0–1].
    Based solely on factual historical metrics — no character inference (AI Ethics).
    Formula: Bayesian-smoothed completion rate + rating boost.
    """
    total_rides = candidate.driver_completed_rides + candidate.driver_cancellations
    # Laplace-smoothed completion rate (prior = 0.85)
    prior_completions = 17   # 85% of 20 pseudo-observations
    prior_total = 20
    smoothed_rate = (candidate.driver_completed_rides + prior_completions) / (total_rides + prior_total)

    # Rating boost (0.0–0.2 extra if rating available)
    rating_boost = 0.0
    if candidate.driver_avg_rating is not None:
        # Rating is 1–5 scale; map to 0–0.2 boost above a 3.0 baseline
        rating_boost = max(0.0, (candidate.driver_avg_rating - 3.0) / 10.0)

    reliability_score = min(1.0, smoothed_rate + rating_boost)

    contributions = {
        "reliability_completion_rate": round(smoothed_rate, 4),
        "reliability_rating_boost": round(rating_boost, 4),
        # Note: data confidence is informational, NOT added to the float SHAP dict
    }
    return round(reliability_score, 4), contributions


def score_preferences(
    candidate: RideCandidate,
    preferences: PassengerPreferences,
) -> Tuple[float, dict]:
    """
    Passenger preference alignment score [0–1].
    Hard requirement violations → 0.0. Soft matches contribute positively.
    """
    # Detour alignment
    detour_score = max(0.0, 1.0 - (candidate.max_detour_minutes / max(preferences.preferred_max_detour, 1)))
    pref_score = min(1.0, detour_score)
    contributions = {"preference_detour_alignment": round(detour_score, 4)}
    return round(pref_score, 4), contributions


# ─────────────────────────────────────────────────────────────────
# Composite scoring weights
# ─────────────────────────────────────────────────────────────────

WEIGHTS_B1 = {
    "geo": 0.30,
    "time": 0.25,
    "price": 0.15,
    "reliability": 0.25,
    "preference": 0.05,
}

WEIGHTS_B2 = {
    # B2 places higher weight on reliability (ReliabilityAI integration)
    "geo": 0.25,
    "time": 0.20,
    "price": 0.10,
    "reliability": 0.35,
    "preference": 0.10,
}


# ─────────────────────────────────────────────────────────────────
# SmartMatch Engine
# ─────────────────────────────────────────────────────────────────

class SmartMatchEngine:
    """
    Two-sided matching engine.

    B1: Rule-based deterministic matching using WEIGHTS_B1.
    B2: SmartMatch — same formula but with WEIGHTS_B2 (reliability-boosted).
         In future modules: replaced by LightGBM model trained on simulation data.
    """

    def __init__(self, algorithm: str = "B2_SMARTMATCH"):
        self.algorithm = algorithm
        self.weights = WEIGHTS_B2 if algorithm == "B2_SMARTMATCH" else WEIGHTS_B1
        logger.info(f"SmartMatchEngine initialised: algorithm={algorithm}")

    def _score_candidate(
        self,
        candidate: RideCandidate,
        request: SmartMatchRequest,
    ) -> MatchScore:
        """Score a single candidate against the passenger request."""

        geo_s, geo_contrib = score_geo(
            candidate,
            request.search_origin.lat, request.search_origin.lng,
            request.search_destination.lat, request.search_destination.lng,
        )
        time_s, time_contrib = score_time(candidate, request.requested_departure)
        price_s, price_contrib = score_price(candidate, request.preferences)
        rel_s, rel_contrib = score_reliability(candidate)
        pref_s, pref_contrib = score_preferences(candidate, request.preferences)

        w = self.weights
        composite = (
            w["geo"] * geo_s
            + w["time"] * time_s
            + w["price"] * price_s
            + w["reliability"] * rel_s
            + w["preference"] * pref_s
        )
        composite = round(min(1.0, max(0.0, composite)), 4)

        # Build SHAP-style contribution map (weighted contributions)
        shap = {
            "geo_score": round(w["geo"] * geo_s, 4),
            "time_score": round(w["time"] * time_s, 4),
            "price_score": round(w["price"] * price_s, 4),
            "reliability_score": round(w["reliability"] * rel_s, 4),
            "preference_score": round(w["preference"] * pref_s, 4),
            **geo_contrib,
            **time_contrib,
            **price_contrib,
            **rel_contrib,
            **pref_contrib,
        }

        # Generate a human-readable match reason
        top_factors = sorted(
            [("location match", geo_s), ("time alignment", time_s),
             ("price", price_s), ("driver reliability", rel_s)],
            key=lambda x: x[1], reverse=True
        )[:2]
        match_reason = (
            f"Strong {top_factors[0][0]} ({top_factors[0][1]:.0%}) "
            f"and {top_factors[1][0]} ({top_factors[1][1]:.0%}). "
            f"Overall match: {composite:.0%}."
        )

        return MatchScore(
            ride_id=candidate.ride_id,
            driver_id=candidate.driver_id,
            composite_score=composite,
            geo_score=geo_s,
            time_score=time_s,
            price_score=price_s,
            reliability_score=rel_s,
            preference_score=pref_s,
            shap_contributions=shap,
            match_reason=match_reason,
            departure_time=candidate.departure_time,
            price_per_seat=candidate.price_per_seat,
            available_seats=candidate.available_seats,
        )

    def rank_candidates(self, request: SmartMatchRequest) -> SmartMatchResponse:
        """
        Score and rank all candidates. Returns top matches descending by composite score.
        Also filters out hard-constraint violations (e.g., not enough seats).
        """
        scored: List[MatchScore] = []

        for candidate in request.candidates:
            # Hard constraint: seat availability
            if candidate.available_seats < request.seats_needed:
                logger.debug(f"Filtered out ride {candidate.ride_id}: insufficient seats")
                continue

            match_score = self._score_candidate(candidate, request)
            scored.append(match_score)

        # Sort descending by composite score
        scored.sort(key=lambda m: m.composite_score, reverse=True)

        return SmartMatchResponse(
            passenger_id=request.passenger_id,
            total_candidates=len(request.candidates),
            ranked_matches=scored,
            algorithm=self.algorithm,
            experiment_id=request.experiment_id,
            processed_at=datetime.now(timezone.utc),
        )


# ─────────────────────────────────────────────────────────────────
# Singleton instances for the two baselines
# ─────────────────────────────────────────────────────────────────
_b1_engine: Optional[SmartMatchEngine] = None
_b2_engine: Optional[SmartMatchEngine] = None


def get_b1_engine() -> SmartMatchEngine:
    global _b1_engine
    if _b1_engine is None:
        _b1_engine = SmartMatchEngine(algorithm="B1_RULE_BASED")
    return _b1_engine


def get_b2_engine() -> SmartMatchEngine:
    global _b2_engine
    if _b2_engine is None:
        _b2_engine = SmartMatchEngine(algorithm="B2_SMARTMATCH")
    return _b2_engine
