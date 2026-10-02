"""
VAYORA AI Service — Admin Analytics & Research Dashboard (Phase 9)
GET /ai/admin/analytics/kpis   →  Aggregated KPIs for research dashboard
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/admin/analytics/kpis",
    summary="Phase 9: Admin Research Dashboard KPIs",
    description="Fetches aggregated KPI metrics from the ml_predictions and event_logs tables.",
    tags=["Admin"],
)
async def get_kpis(
    experiment_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns aggregated research metrics for the dashboard:
    - Average match score
    - Recovery rate
    - Demand gap severity
    - Optimization improvements
    """
    
    # 1. AI Predictions Summary
    query_predictions = text("""
        SELECT 
            model_name, 
            COUNT(*) as total_predictions,
            AVG(prediction_value) as avg_score
        FROM ml_predictions
        WHERE is_simulation = TRUE
          AND (:exp_id IS NULL OR experiment_id = :exp_id)
        GROUP BY model_name
    """)
    
    res_preds = await db.execute(query_predictions, {"exp_id": experiment_id})
    models_summary = [
        {
            "model": row.model_name,
            "total_predictions": row.total_predictions,
            "avg_score": round(float(row.avg_score), 4) if row.avg_score else 0.0
        }
        for row in res_preds.fetchall()
    ]

    # 2. Event Logs Summary (e.g. optimizations, recoveries)
    query_events = text("""
        SELECT 
            event_type, 
            COUNT(*) as event_count
        FROM event_logs
        WHERE (:exp_id IS NULL OR payload->>'experiment_id' = :exp_id)
        GROUP BY event_type
    """)
    
    res_events = await db.execute(query_events, {"exp_id": experiment_id})
    events_summary = [
        {
            "event": row.event_type,
            "count": row.event_count
        }
        for row in res_events.fetchall()
    ]

    return {
        "timestamp": datetime.now(timezone.utc),
        "experiment_filter": experiment_id or "ALL",
        "models_summary": models_summary,
        "events_summary": events_summary,
        "is_simulation_mode": True
    }
