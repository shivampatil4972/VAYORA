"""
VAYORA AI Service — DemandAI Engine (B5)
==========================================
Predicts supply-demand gaps across geographic zones and time windows,
generates driver nudges to reposition toward high-demand areas.

Research Baseline B5 = B4 (ReliabilityAI) + DemandAI

Key signals used:
  1. Zero-result searches (ride_requests.is_fulfilled = FALSE) — strongest signal
  2. Historical booking density by zone and hour
  3. Day-of-week patterns
  4. Time-of-day demand curves (rush hours, early morning intercity, etc.)

Outputs:
  - DemandPrediction: expected_demand, expected_supply, gap_score per zone
  - DriverNudge: personalized suggestion to driver to reposition
  - DemandHeatmap: grid of demand scores for frontend visualization

Data source labeling: All predictions labeled SIMULATION until pilot data available.
No personal passenger data used in predictions — only aggregate anonymized counts.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)

MODEL_VERSION = "heuristic-demand-v1.0"


# ─────────────────────────────────────────────────────────────────
# Zone representation (H3-lite: simple lat/lng grid cells)
# ─────────────────────────────────────────────────────────────────

@dataclass
class GeoZone:
    """A geographic demand zone (grid cell)."""
    zone_id: str            # e.g. "16.7_74.2" (1-decimal grid)
    center_lat: float
    center_lng: float
    radius_km: float = 5.0  # zone radius


def lat_lng_to_zone(lat: float, lng: float, precision: int = 1) -> str:
    """Map a coordinate to a grid zone ID at given decimal precision."""
    return f"{round(lat, precision)}_{round(lng, precision)}"


def zone_center(zone_id: str) -> Tuple[float, float]:
    """Recover the center lat/lng from a zone ID."""
    parts = zone_id.split("_")
    return float(parts[0]), float(parts[1])


# ─────────────────────────────────────────────────────────────────
# Demand signal computation
# ─────────────────────────────────────────────────────────────────

@dataclass
class HistoricalRecord:
    """
    One aggregated demand record from the database.
    Built from ride_requests — including unfulfilled ones.
    """
    zone_id: str
    hour_of_day: int
    day_of_week: int
    total_searches: int
    fulfilled_searches: int
    unfulfilled_searches: int
    total_rides_offered: int


def compute_fulfillment_rate(record: HistoricalRecord) -> float:
    """Fraction of searches that resulted in a booking."""
    if record.total_searches == 0:
        return 0.5   # neutral prior
    return record.fulfilled_searches / record.total_searches


def compute_gap_score(record: HistoricalRecord) -> float:
    """
    Gap score [0–1]: how severe is the supply–demand mismatch?
    1.0 = critical gap (many searches, no rides)
    0.0 = well-served zone
    """
    if record.total_searches == 0:
        return 0.0
    unfulfilled_ratio = record.unfulfilled_searches / record.total_searches
    # Amplify if absolute unfulfilled count is high (volume matters)
    volume_weight = min(1.0, record.total_searches / 50.0)
    return round(unfulfilled_ratio * volume_weight, 4)


# ─────────────────────────────────────────────────────────────────
# Time-of-day demand curve (intercity-specific)
# ─────────────────────────────────────────────────────────────────

# Peak demand multipliers by hour (0-23), calibrated for intercity shared mobility
HOURLY_DEMAND_CURVE = {
    0: 0.2, 1: 0.1, 2: 0.1, 3: 0.2, 4: 0.5,
    5: 0.8, 6: 1.0, 7: 1.2, 8: 1.1, 9: 0.9,
    10: 0.7, 11: 0.6, 12: 0.7, 13: 0.6, 14: 0.5,
    15: 0.6, 16: 0.8, 17: 1.1, 18: 1.2, 19: 1.0,
    20: 0.8, 21: 0.6, 22: 0.4, 23: 0.3,
}

# Day-of-week multipliers (0=Monday, 6=Sunday)
DOW_MULTIPLIERS = {0: 0.9, 1: 0.85, 2: 0.85, 3: 0.9, 4: 1.1, 5: 1.2, 6: 1.0}


def baseline_demand(hour: int, dow: int, base_rate: float = 10.0) -> float:
    """
    Heuristic baseline demand estimate for a zone at a given time.
    Returns expected number of passenger searches per hour.
    PUBLIC_CALIBRATION source (calibrated from typical intercity patterns).
    """
    return base_rate * HOURLY_DEMAND_CURVE.get(hour, 0.5) * DOW_MULTIPLIERS.get(dow, 1.0)


# ─────────────────────────────────────────────────────────────────
# DemandAI prediction data classes
# ─────────────────────────────────────────────────────────────────

@dataclass
class DemandPrediction:
    zone_id: str
    center_lat: float
    center_lng: float
    prediction_hour: int
    day_of_week: int
    expected_demand: float          # Predicted searches per hour
    expected_supply: float          # Predicted available rides
    gap_score: float                # 0-1, higher = worse gap
    fulfillment_rate: float         # Historical fill rate
    confidence: str                 # LOW / MEDIUM / HIGH
    data_source: str = "SIMULATION" # AI Ethics / data labeling
    model_version: str = MODEL_VERSION


@dataclass
class DriverNudge:
    """
    A personalized nudge to a driver to reposition toward high-demand zones.
    Always framed as a suggestion — driver retains full autonomy (AI Ethics).
    """
    driver_id: UUID
    current_zone: str
    target_zone: str
    target_lat: float
    target_lng: float
    distance_km: float
    demand_gap_score: float
    expected_demand: float
    nudge_message: str
    urgency: str                    # LOW / MEDIUM / HIGH
    is_simulation: bool = True


@dataclass
class HeatmapCell:
    """One cell in the demand heatmap for frontend visualization."""
    lat: float
    lng: float
    demand_score: float             # 0.0–1.0 normalized
    gap_score: float
    label: str                      # "HIGH DEMAND", "MODERATE", "WELL SERVED"


@dataclass
class DemandHeatmap:
    cells: List[HeatmapCell]
    generated_at: datetime
    hour: int
    day_of_week: int
    is_simulation: bool = True


# ─────────────────────────────────────────────────────────────────
# DemandAI Engine
# ─────────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class DemandAIEngine:
    """
    DemandAI: predicts supply-demand gaps and generates driver nudges.

    Phase 6 (heuristic version):
      - Uses historical HistoricalRecord inputs (from DB query layer)
      - Combines calibrated time-of-day curves with historical fill rates
      - Generates per-zone DemandPredictions
      - Identifies top gap zones and generates DriverNudges

    Phase 6+ (LightGBM upgrade):
      - Replaces heuristic with trained regression model on simulation data
    """

    def predict_zone_demand(
        self,
        records: List[HistoricalRecord],
        target_hour: int,
        target_dow: int,
    ) -> List[DemandPrediction]:
        """Generate demand predictions for each zone based on historical records."""
        predictions: List[DemandPrediction] = []

        for record in records:
            # Historical fill rate with Laplace smoothing
            fill_rate = (record.fulfilled_searches + 1) / (record.total_searches + 2)

            # Baseline demand adjusted by time-of-day
            base = baseline_demand(target_hour, target_dow, base_rate=15.0)

            # Adjust with historical data
            if record.total_searches > 0:
                hist_factor = record.total_searches / max(baseline_demand(record.hour_of_day, record.day_of_week, 15.0), 1)
                expected_demand = base * min(2.0, max(0.3, hist_factor))
            else:
                expected_demand = base

            expected_supply = record.total_rides_offered * HOURLY_DEMAND_CURVE.get(target_hour, 0.5)
            gap = compute_gap_score(record)

            # Confidence based on data volume
            if record.total_searches < 5:
                confidence = "LOW"
            elif record.total_searches < 30:
                confidence = "MEDIUM"
            else:
                confidence = "HIGH"

            center_lat, center_lng = zone_center(record.zone_id)

            predictions.append(DemandPrediction(
                zone_id=record.zone_id,
                center_lat=center_lat,
                center_lng=center_lng,
                prediction_hour=target_hour,
                day_of_week=target_dow,
                expected_demand=round(expected_demand, 2),
                expected_supply=round(expected_supply, 2),
                gap_score=gap,
                fulfillment_rate=round(fill_rate, 4),
                confidence=confidence,
                data_source="SIMULATION",
                model_version=MODEL_VERSION,
            ))

        return sorted(predictions, key=lambda p: p.gap_score, reverse=True)

    def generate_nudges(
        self,
        predictions: List[DemandPrediction],
        driver_id: UUID,
        driver_lat: float,
        driver_lng: float,
        max_nudge_km: float = 30.0,
        top_n: int = 3,
    ) -> List[DriverNudge]:
        """
        Generate driver repositioning nudges toward high-gap zones.
        Only zones within max_nudge_km radius are considered.
        Suggestions only — driver always retains choice (AI Ethics).
        """
        nudges: List[DriverNudge] = []
        driver_zone = lat_lng_to_zone(driver_lat, driver_lng)

        # Filter to high-gap zones within reach
        reachable = [
            p for p in predictions
            if (p.gap_score > 0.2
                and _haversine_km(driver_lat, driver_lng, p.center_lat, p.center_lng) <= max_nudge_km
                and p.zone_id != driver_zone)
        ]
        reachable.sort(key=lambda p: p.gap_score, reverse=True)

        for pred in reachable[:top_n]:
            dist_km = _haversine_km(driver_lat, driver_lng, pred.center_lat, pred.center_lng)

            if pred.gap_score > 0.6:
                urgency = "HIGH"
                msg_prefix = "🔴 High demand alert"
            elif pred.gap_score > 0.35:
                urgency = "MEDIUM"
                msg_prefix = "🟡 Demand opportunity"
            else:
                urgency = "LOW"
                msg_prefix = "🟢 Suggested area"

            message = (
                f"{msg_prefix}: ~{pred.expected_demand:.0f} searches/hr near "
                f"({pred.center_lat:.2f}, {pred.center_lng:.2f}), "
                f"{dist_km:.1f} km away. "
                f"Current supply coverage: {pred.fulfillment_rate:.0%}. "
                f"[SIMULATION — suggestion only]"
            )

            nudges.append(DriverNudge(
                driver_id=driver_id,
                current_zone=driver_zone,
                target_zone=pred.zone_id,
                target_lat=pred.center_lat,
                target_lng=pred.center_lng,
                distance_km=round(dist_km, 2),
                demand_gap_score=pred.gap_score,
                expected_demand=pred.expected_demand,
                nudge_message=message,
                urgency=urgency,
                is_simulation=True,
            ))

        return nudges

    def generate_heatmap(
        self,
        predictions: List[DemandPrediction],
    ) -> DemandHeatmap:
        """Generate a normalized demand heatmap for frontend visualization."""
        if not predictions:
            return DemandHeatmap(cells=[], generated_at=datetime.now(timezone.utc),
                                  hour=0, day_of_week=0)

        max_demand = max(p.expected_demand for p in predictions) or 1.0
        hour = predictions[0].prediction_hour
        dow = predictions[0].day_of_week
        cells: List[HeatmapCell] = []

        for pred in predictions:
            score = pred.expected_demand / max_demand
            if pred.gap_score > 0.5:
                label = "HIGH DEMAND GAP"
            elif pred.gap_score > 0.25:
                label = "MODERATE GAP"
            elif score > 0.7:
                label = "WELL SERVED"
            else:
                label = "LOW ACTIVITY"

            cells.append(HeatmapCell(
                lat=pred.center_lat,
                lng=pred.center_lng,
                demand_score=round(score, 4),
                gap_score=pred.gap_score,
                label=label,
            ))

        return DemandHeatmap(
            cells=cells,
            generated_at=datetime.now(timezone.utc),
            hour=hour,
            day_of_week=dow,
            is_simulation=True,
        )


# ─────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────
_demand_engine: Optional[DemandAIEngine] = None


def get_demand_engine() -> DemandAIEngine:
    global _demand_engine
    if _demand_engine is None:
        _demand_engine = DemandAIEngine()
        logger.info("DemandAI engine initialised: model_version=%s", MODEL_VERSION)
    return _demand_engine
