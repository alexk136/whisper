#!/usr/bin/env python3
"""
Main entry point for the Whisper Voice Authentication microservice.
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.routes import api_router
from app.api.hybrid_routes import hybrid_router
from app.utils.config import load_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Create FastAPI application
app = FastAPI(
    title="Whisper Voice Auth",
    description="Voice Authentication and Analysis Microservice",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("cors", {}).get("origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(hybrid_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with system status."""
    try:
        from datetime import datetime
        from app.hybrid.controller import get_hybrid_status
        
        return {
            "status": "healthy",
            "service": "whisper",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "api": "ready",
                "hybrid_stt": "ready",
                "voice_auth": "ready"
            },
            "system_status": get_hybrid_status()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Whisper Voice Authentication",
        "description": "Voice Authentication and Analysis Microservice with Hybrid STT",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting Whisper Voice Auth service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=config.get("development_mode", False),
    )
