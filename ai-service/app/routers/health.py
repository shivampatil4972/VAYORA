"""Health check router — Module 0 skeleton."""
import time
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])

START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    uptime_seconds: float


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """
    Returns service health status.
    Used by Docker Compose health probes and monitoring.
    """
    return HealthResponse(
        status="UP",
        service="vayora-ai-service",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=round(time.time() - START_TIME, 2),
    )
