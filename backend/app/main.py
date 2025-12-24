"""
TherapyBridge Backend API
FastAPI application with Supabase + Breakthrough Detection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.routers import sessions, demo, debug, sse

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TherapyBridge API",
    description="AI-powered therapy session management with breakthrough detection",
    version="1.0.0",
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions.router)
app.include_router(demo.router)
app.include_router(debug.router)
app.include_router(sse.router)

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TherapyBridge API",
        "version": "1.0.1",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "breakthrough_detection": "enabled" if settings.openai_api_key else "disabled"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting TherapyBridge API")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   Debug mode: {settings.debug}")
    logger.info(f"   Supabase URL: {settings.supabase_url}")
    logger.info(f"   Breakthrough detection: {'✓ Enabled' if settings.openai_api_key else '✗ Disabled'}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down TherapyBridge API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
