"""
TherapyBridge Backend API
FastAPI application with Supabase + Breakthrough Detection
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.routers import sessions, demo, debug, sse
from app.database import get_db
from supabase import Client

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


@app.get("/api/patients/{patient_id}/roadmap")
async def get_patient_roadmap(
    patient_id: str,
    db: Client = Depends(get_db)
):
    """
    Get patient's latest roadmap data (PR #3: Your Journey Dynamic Roadmap)

    Fetches the current roadmap from patient_roadmap table.
    Returns 404 if no roadmap exists yet (0 sessions analyzed).
    """
    try:
        # Query patient_roadmap table
        result = db.table("patient_roadmap") \
            .select("roadmap_data, metadata") \
            .eq("patient_id", patient_id) \
            .execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="No roadmap found for this patient. Sessions need to be analyzed first."
            )

        roadmap_record = result.data[0]

        return {
            "roadmap": roadmap_record["roadmap_data"],
            "metadata": roadmap_record["metadata"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch roadmap for patient {patient_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch roadmap: {str(e)}"
        )


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
