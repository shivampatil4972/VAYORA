"""
VAYORA AI Service — ReliabilityAI Engine (B4)
================================================
Predicts P(cancel) and P(complete) for a driver-ride pair.

Architecture:
  - Phase 3: Heuristic model using Bayesian-smoothed cancellation rate + ride features
  - Phase 5+ (Module 16): LightGBM model trained on simulation data

All predictions are LABELED as SIMULATION data (AI Ethics / Data Source Labeling).
No character inferences — only factual operational metrics.
"""
from __future__ import annotations

import math
import logging
from datetime import timezone
from typing import Optional, Dict, Tuple

from app.schemas.ai_schemas import ReliabilityFeatures, ReliabilityPrediction

logger = logging.getLogger(__name__)

MODEL_VERSION = "heuristic-v1.0"


# ─────────────────────────────────────────────────────────────────
# Feature engineering helpers
# ─────────────────────────────────────────────────────────────────

def _cancellation_rate(completed: int, cancellations: int) -> float:
    """Bayesian-smoothed cancellation rate (Laplace prior: 5% cancellation)."""
    prior_cancel = 1   # 5% of 20
    prior_total = 20
    total = completed + cancellations
    return (cancellations + prior_cancel) / (total + prior_total)


def _time_of_day_risk(hour: int) -> float:
    """
    Early morning (4–7am) rides have higher non-completion risk.
    Returns a risk multiplier [1.0 = neutral, >1 = higher risk].
    """
    if 4 <= hour <= 6:
        return 1.3   # Very early morning
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        return 0.9   # Rush hour — drivers more committed
    return 1.0


def _experience_factor(completed: int) -> float:
    """
    Experienced drivers are more reliable.
    Returns a reliability multiplier [0.8 = new, 1.0 = experienced].
    """
    if completed < 5:
        return 0.80   # New driver: higher uncertainty → conservative
    if completed < 20:
        return 0.90
    if completed < 50:
        return 0.97
    return 1.00


def _day_of_week_factor(dow: int) -> float:
    """Day-of-week completion rate modifier (0=Mon, 6=Sun)."""
    # Weekend rides slightly higher risk (leisure motivation)
    weekend_risk = {5: 1.05, 6: 1.08}
    return weekend_risk.get(dow, 1.0)


# ─────────────────────────────────────────────────────────────────
# Reliability Band Classification
# ─────────────────────────────────────────────────────────────────

def _classify_band(p_cancel: float) -> str:
    if p_cancel < 0.05:
        return "VERY_RELIABLE"
    if p_cancel < 0.12:
        return "RELIABLE"
    if p_cancel < 0.25:
        return "MODERATE"
    return "RISKY"


def _classify_confidence(total_rides: int) -> str:
    if total_rides < 5:
        return "LOW"
    if total_rides < 25:
        return "MEDIUM"
    return "HIGH"


# ─────────────────────────────────────────────────────────────────
# Heuristic ReliabilityAI Model
# ─────────────────────────────────────────────────────────────────

class ReliabilityAIEngine:
    """
    Heuristic reliability predictor (Phase 3 / B4 baseline).

    Combines:
    1. Bayesian-smoothed cancellation rate from history
    2. Time-of-day risk adjustment
    3. Experience factor (data volume)
    4. Day-of-week adjustment
    5. Distance penalty (very long rides → more risk)

    Outputs P_CANCEL in [0, 1] with SHAP-style contributions.
    """

    def predict(self, features: ReliabilityFeatures) -> ReliabilityPrediction:
        """Predict P(cancel) for a driver-ride pair."""

        # ── Base cancellation probability ──────────────────────────
        base_p_cancel = _cancellation_rate(
            features.completed_rides,
            features.cancellations
        )

        # ── Adjustment factors ─────────────────────────────────────
        time_risk = _time_of_day_risk(features.hour_of_day)
        exp_factor = _experience_factor(features.completed_rides)
        dow_factor = _day_of_week_factor(features.day_of_week)

        # Long-distance penalty: rides >200km have +3% base risk
        distance_factor = 1.0
        if features.distance_km > 200:
            distance_factor = 1.0 + min(0.1, (features.distance_km - 200) / 1000)

        # Inactivity penalty: >30 days since last ride → +5% risk
        inactivity_factor = 1.0
        if features.days_since_last_ride and features.days_since_last_ride > 30:
            inactivity_factor = 1.05
        elif features.days_since_last_ride and features.days_since_last_ride > 60:
            inactivity_factor = 1.10

        # ── Composite P_CANCEL ─────────────────────────────────────
        adjusted_p_cancel = (
            base_p_cancel
            * time_risk
            * (1.0 / max(exp_factor, 0.01))
            * dow_factor
            * distance_factor
            * inactivity_factor
        )
        p_cancel = round(min(1.0, max(0.0, adjusted_p_cancel)), 4)
        p_complete = round(1.0 - p_cancel, 4)

        # ── SHAP-style contributions ───────────────────────────────
        total_rides = features.completed_rides + features.cancellations
        base_contribution = round(base_p_cancel, 4)

        shap = {
            "base_cancellation_rate": base_contribution,
            "time_of_day_adjustment": round((time_risk - 1.0) * base_p_cancel, 4),
            "experience_adjustment": round(((1.0 / max(exp_factor, 0.01)) - 1.0) * base_p_cancel, 4),
            "day_of_week_adjustment": round((dow_factor - 1.0) * base_p_cancel, 4),
            "distance_adjustment": round((distance_factor - 1.0) * base_p_cancel, 4),
            "inactivity_adjustment": round((inactivity_factor - 1.0) * base_p_cancel, 4),
        }

        # ── Classification ─────────────────────────────────────────
        band = _classify_band(p_cancel)
        confidence = _classify_confidence(total_rides)

        # ── Human-readable explanation ─────────────────────────────
        explanation = self._build_explanation(features, p_cancel, band, confidence, shap)

        return ReliabilityPrediction(
            driver_id=features.driver_id,
            ride_id=features.ride_id,
            p_cancel=p_cancel,
            p_complete=p_complete,
            confidence=confidence,
            reliability_band=band,
            shap_contributions=shap,
            explanation=explanation,
            model_version=MODEL_VERSION,
            is_simulation=True,  # SIMULATION label — AI Ethics
            experiment_id=features.experiment_id,
        )

    def _build_explanation(
        self,
        features: ReliabilityFeatures,
        p_cancel: float,
        band: str,
        confidence: str,
        shap: Dict[str, float],
    ) -> str:
        """Build a plain-language explanation. This is a prediction, not a guarantee."""
        total = features.completed_rides + features.cancellations
        parts = [
            f"Based on {total} historical rides, this driver has an estimated "
            f"{p_cancel:.1%} cancellation probability ({band}).",
        ]
        if confidence == "LOW":
            parts.append("Confidence is LOW due to limited ride history.")
        top_factor = max(shap.items(), key=lambda x: abs(x[1]))
        if abs(top_factor[1]) > 0.01:
            parts.append(f"Top contributing factor: {top_factor[0].replace('_', ' ')}.")
        parts.append("Note: This is a SIMULATION-labeled prediction, not a guarantee.")
        return " ".join(parts)


# ─────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────
_reliability_engine: Optional[ReliabilityAIEngine] = None


def get_reliability_engine() -> ReliabilityAIEngine:
    global _reliability_engine
    if _reliability_engine is None:
        _reliability_engine = ReliabilityAIEngine()
        logger.info("ReliabilityAI engine initialised: model_version=%s", MODEL_VERSION)
    return _reliability_engine
