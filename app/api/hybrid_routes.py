"""
Hybrid STT API routes for the Whisper Voice Auth microservice.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Header, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging
import os
from pathlib import Path

from app.api.schemas import HybridSTTResponse, ErrorResponse
from app.audio.processor import process_audio_file
from app.hybrid.controller import process_audio_hybrid
from app.utils.security import validate_api_key

logger = logging.getLogger(__name__)

# Create router
hybrid_router = APIRouter()


@hybrid_router.post(
    "/hybrid/stt",
    response_model=HybridSTTResponse,
    responses={
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
    description="Process audio using hybrid STT approach (local with remote fallback).",
)
async def hybrid_stt(
    audio_file: UploadFile = File(...),
    audio_url: Optional[str] = None,
    verify_speaker: bool = Query(False, description="Whether to verify speaker identity"),
    return_debug: bool = Query(False, description="Include debug information in response"),
    use_semantics: bool = Query(False, description="Use semantic validation for comparing results"),
    semantic_threshold: Optional[float] = Query(None, description="Semantic similarity threshold (0.0-1.0)"),
    api_key: str = Depends(validate_api_key),
) -> HybridSTTResponse:
    """
    Process audio using hybrid STT approach with local processing and remote fallback.
    
    Args:
        audio_file: Uploaded audio file (WAV, MP3, etc.)
        audio_url: URL to audio file (alternative to upload)
        verify_speaker: Whether to verify speaker identity
        return_debug: Whether to include debug information in response
        use_semantics: Whether to use semantic validation
        semantic_threshold: Semantic similarity threshold
        api_key: API key for service authentication
        
    Returns:
        HybridSTTResponse: The STT result with text and metadata
    """
    try:
        # Set environment variables for configuration
        if use_semantics:
            os.environ["WHISPER_HYBRID_STT_USE_SEMANTIC_VALIDATION"] = "true"
        
        if semantic_threshold is not None:
            os.environ["WHISPER_HYBRID_STT_SEMANTIC_THRESHOLD"] = str(semantic_threshold)
        
        # Process and normalize the audio file
        processed_audio_path = await process_audio_file(audio_file, audio_url)
        
        # Process with hybrid approach
        result = await process_audio_hybrid(
            audio_path=processed_audio_path,
            verify_speaker_flag=verify_speaker,
            return_debug=return_debug
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing hybrid STT: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error processing audio: {str(e)}"
        )
