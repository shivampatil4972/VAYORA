"""
VAYORA AI Service — FastAPI Application Entry Point
"""
import logging
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import health, smartmatch, reliability, optimize, recovery, demand, ev, admin_analytics

settings = get_settings()

# Configure structured logging
logging.basicConfig(level=settings.ai_log_level.upper())
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.ai_log_level.upper(), logging.INFO)
    )
)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle — warm up AI engines."""
    logger.info("VAYORA AI Service starting", version="0.1.0")
    # Warm up singletons so first request isn't slow
    from app.services.smartmatch import get_b1_engine, get_b2_engine
    from app.services.reliability import get_reliability_engine
    get_b1_engine()
    get_b2_engine()
    get_reliability_engine()
    from app.services.optimizer import get_optimizer
    from app.services.recovery import get_recovery_engine
    get_optimizer()
    get_recovery_engine()
    from app.services.demand import get_demand_engine
    from app.services.ev_feasibility import get_ev_engine
    get_demand_engine()
    get_ev_engine()
    logger.info("AI engines warmed up: SmartMatch (B1/B2), ReliabilityAI, Optimizer, RecoveryMatch, DemandAI, EV")
    yield
    logger.info("VAYORA AI Service stopping")


app = FastAPI(
    title="VAYORA AI Service",
    description=(
        "AI/ML backend for VAYORA — SmartMatch, ReliabilityAI, "
        "DemandAI, RecoveryMatch, EV Intelligence, Optimization"
    ),
    version="0.1.0",
    lifespan=lifespan,
    # Disable docs in production via config
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(smartmatch.router, prefix="/ai", tags=["SmartMatch"])       # Phase 3 — B1/B2
app.include_router(reliability.router, prefix="/ai", tags=["ReliabilityAI"])   # Phase 3 — B4
app.include_router(optimize.router, prefix="/ai", tags=["Optimization"])       # Phase 4 — B3
app.include_router(recovery.router, prefix="/ai", tags=["Recovery"])           # Phase 5 — B6
app.include_router(demand.router, prefix="/ai", tags=["DemandAI"])             # Phase 6 — B5
app.include_router(ev.router, prefix="/ai", tags=["EV"])                       # Phase 7 — B7
app.include_router(admin_analytics.router, prefix="/ai", tags=["Admin"])       # Phase 9
