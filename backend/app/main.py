"""
TherapyBridge Backend API
FastAPI application for therapy session management and AI note extraction
"""
import os
import time
import logging
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from sqlalchemy import text
from openai import AsyncOpenAI

from app.database import init_db, close_db, engine, AsyncSessionLocal
from app.routers import sessions, patients, cleanup, analytics, export, goal_tracking, assessments, self_report, progress_reports, templates, notes, mfa
# Temporarily commented out - incomplete features
# from app.routers import treatment_plans, goals, interventions
from app.auth.router import router as auth_router
from app.middleware.rate_limit import limiter, custom_rate_limit_handler
from app.middleware.error_handler import register_exception_handlers
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.logging_config import setup_logging
from app.services.cleanup import run_startup_cleanup
from app.services.template_seeder import seed_on_startup

# Feature 8: HIPAA Compliance Security Middleware
from app.middleware.audit import AuditMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

# Feature 8: HIPAA Compliance Routers
from app.routers import session_security, audit, access_requests, emergency, consent

# Analytics scheduler imports
from app.scheduler import start_scheduler, shutdown_scheduler
from app.tasks.aggregation import register_analytics_jobs

load_dotenv()

# Configure structured logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
JSON_LOGS = os.getenv("JSON_LOGS", "false").lower() in ("true", "1", "yes")
setup_logging(log_level=LOG_LEVEL, json_format=JSON_LOGS)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    Runs database checks, initializes services, and starts scheduler on startup.
    """
    # Startup
    logger.info("🚀 Starting TherapyBridge API")
    await init_db()
    logger.info("✅ Database initialized")

    # Seed system templates
    async with AsyncSessionLocal() as db:
        await seed_on_startup(db)

    # Run cleanup on startup if enabled
    await run_startup_cleanup()

    # Start analytics scheduler and register background jobs
    logger.info("Starting analytics scheduler...")
    start_scheduler()
    register_analytics_jobs()
    logger.info("✅ Analytics scheduler started and jobs registered")

    yield

    # Shutdown
    logger.info("Shutting down TherapyBridge API")

    # Stop analytics scheduler
    logger.info("Stopping analytics scheduler...")
    shutdown_scheduler()
    logger.info("✅ Analytics scheduler stopped")

    await close_db()
    logger.info("Database connections closed")


# Security: Get debug mode from environment (defaults to False to prevent PHI exposure)
# WARNING: Enabling debug mode will expose Protected Health Information (PHI) in error messages.
# NEVER enable debug mode in production environments.
DEBUG_MODE = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Create FastAPI app
app = FastAPI(
    title="TherapyBridge API",
    description="AI-powered therapy session management and note extraction",
    version="1.0.0",
    lifespan=lifespan,
    debug=DEBUG_MODE  # CRITICAL: Must be False in production to protect patient PHI
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Register global exception handlers
register_exception_handlers(app)

# Middleware order is critical (outermost to innermost):
# 1. SecurityHeaders - Add security headers to all responses (HIPAA compliance)
# 2. AuditMiddleware - Log all requests for HIPAA compliance
# 3. CorrelationId - Add X-Request-ID for tracing
# 4. CORS - Handle cross-origin requests
# 5. Rate limiting - Applied via decorators
# 6. Exception handlers - Catch all errors

# Feature 8: Security headers (first)
app.add_middleware(SecurityHeadersMiddleware)

# Feature 8: Audit logging (after security headers, before CORS)
app.add_middleware(AuditMiddleware)

# Correlation ID middleware (ensure request ID available everywhere)
# This middleware:
# - Accepts X-Request-ID header from clients/proxies
# - Generates UUID if no ID provided
# - Stores ID in context variable for logging and tracing
# - Adds X-Request-ID to response headers
app.add_middleware(CorrelationIdMiddleware)

# CORS middleware (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],  # Allow frontend to read request ID
)

# Include routers
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])

# Feature 8: HIPAA Compliance & Security
app.include_router(mfa.router, prefix="/api/v1/mfa", tags=["Multi-Factor Authentication"])
app.include_router(session_security.router, prefix="/api/v1/auth", tags=["Session Management"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit Logs"])
app.include_router(access_requests.router, prefix="/api/v1/access-requests", tags=["Access Requests"])
app.include_router(emergency.router, prefix="/api/v1/emergency-access", tags=["Emergency Access"])
app.include_router(consent.router, prefix="/api/v1/consent", tags=["Consent Management"])

# Core application routers
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(cleanup.router, prefix="/api/admin", tags=["Cleanup"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(export.router, prefix="/api/v1")

# Goal tracking and progress endpoints (Feature 6)
app.include_router(
    goal_tracking.router,
    prefix="/api/v1",
    tags=["goal-tracking"]
)
app.include_router(
    assessments.router,
    prefix="/api/v1",
    tags=["assessments"]
)
app.include_router(
    self_report.router,
    prefix="/api/v1/self-report",
    tags=["self-report"]
)
app.include_router(
    progress_reports.router,
    prefix="/api/v1/progress-reports",
    tags=["progress-reports"]
)

# Template and note management endpoints (Feature 3)
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(notes.router, prefix="/api/v1", tags=["Session Notes"])

# Treatment plans and goals endpoints (Feature 4)
# Temporarily commented out - incomplete features
# app.include_router(treatment_plans.router, prefix="/api/v1", tags=["Treatment Plans"])
# app.include_router(goals.router, prefix="/api/v1", tags=["Goals"])
# app.include_router(interventions.router, prefix="/api/v1", tags=["Interventions"])


@app.get("/")
async def root():
    """Basic service info endpoint"""
    return {
        "service": "TherapyBridge API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check(response: Response):
    """
    Comprehensive health check endpoint

    Tests:
    - Database connectivity and query execution
    - Database connection pool status
    - OpenAI API connectivity (lightweight check)

    Returns 200 if all services healthy, 503 if any service is degraded
    """
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "checks": {}
    }

    overall_healthy = True

    # Check 1: Database connectivity
    try:
        start = time.time()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_response_time = round((time.time() - start) * 1000, 2)

        # Check connection pool status
        pool_status = {
            "size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
        }

        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": db_response_time,
            "pool": pool_status
        }
    except Exception as e:
        overall_healthy = False
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check 2: OpenAI API connectivity (lightweight - just check if client can be initialized)
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            health_status["checks"]["openai"] = {
                "status": "degraded",
                "message": "API key not configured"
            }
        else:
            # Just verify client can be created (doesn't make actual API call)
            client = AsyncOpenAI(api_key=openai_api_key)
            health_status["checks"]["openai"] = {
                "status": "healthy",
                "message": "Client initialized"
            }
    except Exception as e:
        # Don't fail overall health for OpenAI issues (it's not critical for basic operations)
        health_status["checks"]["openai"] = {
            "status": "degraded",
            "error": str(e)
        }

    # Set overall status and HTTP status code
    if not overall_healthy:
        health_status["status"] = "unhealthy"
        response.status_code = 503

    return health_status


@app.get("/ready")
async def readiness_check(response: Response):
    """
    Kubernetes readiness probe endpoint

    Checks if the service is ready to accept traffic.
    Tests database connectivity only (critical dependency).

    Returns 200 if ready, 503 if not ready
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        response.status_code = 503
        return {
            "status": "not_ready",
            "reason": "database_unavailable",
            "error": str(e)
        }


@app.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint

    Simple check to verify the application is running and not deadlocked.
    Does not test external dependencies.

    Always returns 200 unless the application is completely unresponsive.
    """
    return {
        "status": "alive",
        "timestamp": int(time.time())
    }
