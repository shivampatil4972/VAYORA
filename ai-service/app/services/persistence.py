"""
VAYORA AI Service — ML Prediction Persistence
Saves AI predictions to the ml_predictions table for research KPI tracking.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def save_prediction(
    db: AsyncSession,
    model_name: str,
    model_version: str,
    target_entity_id: uuid.UUID,
    target_entity_type: str,
    prediction_type: str,
    prediction_value: float,
    features_json: Optional[Dict[str, Any]] = None,
    shap_values: Optional[Dict[str, float]] = None,
    experiment_id: Optional[str] = None,
) -> None:
    """
    Persist an ML prediction to the ml_predictions table.
    Called after every SmartMatch / ReliabilityAI prediction.
    """
    try:
        await db.execute(
            text("""
                INSERT INTO ml_predictions
                    (model_name, model_version, target_entity_id, target_entity_type,
                     prediction_type, prediction_value, features_json, shap_values, experiment_id)
                VALUES
                    (:model_name, :model_version, :entity_id, :entity_type,
                     :pred_type, :pred_value, :features::jsonb, :shap::jsonb, :exp_id)
            """),
            {
                "model_name": model_name,
                "model_version": model_version,
                "entity_id": str(target_entity_id),
                "entity_type": target_entity_type,
                "pred_type": prediction_type,
                "pred_value": float(prediction_value),
                "features": json.dumps(features_json) if features_json else "{}",
                "shap": json.dumps(shap_values) if shap_values else "{}",
                "exp_id": experiment_id,
            }
        )
        await db.commit()
    except Exception as exc:
        logger.warning("Failed to persist prediction to DB: %s", exc)
        # Non-fatal: prediction response is still returned even if persistence fails


async def log_event(
    db: AsyncSession,
    event_type: str,
    user_id: Optional[uuid.UUID] = None,
    ride_id: Optional[uuid.UUID] = None,
    booking_id: Optional[uuid.UUID] = None,
    experiment_id: Optional[uuid.UUID] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a system event to event_logs for research KPI tracking (B0–B7).
    """
    try:
        await db.execute(
            text("""
                INSERT INTO event_logs
                    (event_type, user_id, ride_id, booking_id, experiment_id, payload)
                VALUES
                    (:event_type, :user_id, :ride_id, :booking_id, :experiment_id, :payload::jsonb)
            """),
            {
                "event_type": event_type,
                "user_id": str(user_id) if user_id else None,
                "ride_id": str(ride_id) if ride_id else None,
                "booking_id": str(booking_id) if booking_id else None,
                "experiment_id": str(experiment_id) if experiment_id else None,
                "payload": json.dumps(payload) if payload else "{}",
            }
        )
        await db.commit()
    except Exception as exc:
        logger.warning("Failed to log event: %s", exc)
