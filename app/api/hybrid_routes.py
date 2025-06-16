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
    description="Process audio using hybrid STT approach (OpenAI primary, local fallback).",
)
async def hybrid_stt(
    audio_file: UploadFile = File(...),
    audio_url: Optional[str] = None,
    verify_speaker: bool = Query(False, description="Whether to verify speaker identity"),
    return_debug: bool = Query(False, description="Include debug information in response"),
    use_semantics: bool = Query(False, description="Use semantic validation for comparing results"),
    semantic_threshold: Optional[float] = Query(0.8, description="Semantic similarity threshold (0.0-1.0)"),
    language: Optional[str] = Query(None, description="Target language code (e.g., 'en', 'ru')"),
    prompt: Optional[str] = Query(None, description="Context prompt for better transcription"),
    api_key: str = Depends(validate_api_key),
) -> HybridSTTResponse:
    """
    Process audio using hybrid STT approach with OpenAI API primary and local fallback.
    
    Args:
        audio_file: Uploaded audio file (WAV, MP3, etc.)
        audio_url: URL to audio file (alternative to upload)
        verify_speaker: Whether to verify speaker identity
        return_debug: Whether to include debug information in response
        use_semantics: Whether to use semantic validation
        semantic_threshold: Semantic similarity threshold
        language: Target language code
        prompt: Context prompt for better transcription
        api_key: API key for service authentication
        
    Returns:
        HybridSTTResponse: The STT result with text and metadata
    """
    try:
        # Process and normalize the audio file
        processed_audio_path = await process_audio_file(audio_file, audio_url)
        
        # Process with hybrid approach
        result = await process_audio_hybrid(
            audio_path=processed_audio_path,
            verify_speaker_flag=verify_speaker,
            use_semantics=use_semantics,
            semantic_threshold=semantic_threshold or 0.8,
            language=language,
            prompt=prompt,
            return_debug=return_debug
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing hybrid STT: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error processing audio: {str(e)}"
        )


@hybrid_router.post(
    "/hybrid/translate",
    response_model=HybridSTTResponse,
    responses={
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
    description="Translate audio to target language using OpenAI API.",
)
async def translate_audio_endpoint(
    audio_file: UploadFile = File(...),
    audio_url: Optional[str] = None,
    target_language: str = Query("en", description="Target language code (default: 'en')"),
    prompt: Optional[str] = Query(None, description="Context prompt for better translation"),
    return_debug: bool = Query(False, description="Include debug information in response"),
    api_key: str = Depends(validate_api_key),
) -> HybridSTTResponse:
    """
    Translate audio to target language using OpenAI API.
    
    Args:
        audio_file: Uploaded audio file (WAV, MP3, etc.)
        audio_url: URL to audio file (alternative to upload)
        target_language: Target language code
        prompt: Context prompt for better translation
        return_debug: Whether to include debug information
        api_key: API key for service authentication
        
    Returns:
        HybridSTTResponse: Translation result with metadata
    """
    try:
        # Import the translation function
        from app.hybrid.controller import translate_audio_hybrid
        
        # Process and normalize the audio file
        processed_audio_path = await process_audio_file(audio_file, audio_url)
        
        # Translate audio
        result = await translate_audio_hybrid(
            audio_path=processed_audio_path,
            target_language=target_language,
            prompt=prompt,
            return_debug=return_debug
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error translating audio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )
