"""Main FastAPI application"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import upload, transcription, websocket

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Audio Transcription API",
    description="API for audio transcription with speaker diarization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - TEMPORARILY ALLOW ALL for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(transcription.router, prefix="/api", tags=["transcription"])
app.include_router(websocket.router, tags=["websocket"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Audio Transcription API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pipeline_path": str(settings.pipeline_path),
        "upload_dir": str(settings.upload_dir),
        "results_dir": str(settings.results_dir)
    }

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Starting Audio Transcription API")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Results directory: {settings.results_dir}")
    logger.info(f"Pipeline path: {settings.pipeline_path}")
    logger.info(f"Max concurrent jobs: {settings.max_concurrent_jobs}")

    # Set environment variables for pipeline
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.huggingface_token:
        os.environ["HUGGINGFACE_TOKEN"] = settings.huggingface_token

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down Audio Transcription API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug
    )
