"""
OpenAI Whisper API integration for speech recognition.
Primary transcription service with local whisper as fallback.
"""
import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, Union
import openai
from openai import OpenAI
import aiohttp
import asyncio
from app.utils.config import load_config
from app.transcription.speech_recognition import transcribe_audio as local_transcribe

logger = logging.getLogger(__name__)

# Load configuration
config = load_config()
OPENAI_API_KEY = config.get("openai", {}).get("api_key") or os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = config.get("openai", {}).get("model", "gpt-4o-transcribe")
FALLBACK_TO_LOCAL = config.get("transcription", {}).get("fallback_to_local", True)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB limit for OpenAI API

# Initialize OpenAI client
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info(f"OpenAI client initialized with model: {OPENAI_MODEL}")
else:
    openai_client = None
    logger.warning("OpenAI API key not found. Will use local Whisper only.")


async def transcribe_with_openai(
    audio_path: Path,
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    response_format: str = "json"
) -> Tuple[str, float, str]:
    """
    Transcribe audio using OpenAI Whisper API.
    
    Args:
        audio_path: Path to the audio file
        language: Language code (optional, auto-detected if None)
        prompt: Context prompt to improve transcription
        response_format: Output format ("json" or "text")
        
    Returns:
        Tuple[str, float, str]: Transcription text, confidence score, detected language
    """
    if not openai_client:
        raise RuntimeError("OpenAI client not initialized")
    
    # Check file size
    file_size = audio_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size {file_size} exceeds OpenAI limit of {MAX_FILE_SIZE} bytes")
    
    try:
        with open(audio_path, "rb") as audio_file:
            # Prepare transcription parameters
            kwargs = {
                "model": OPENAI_MODEL,
                "file": audio_file,
                "response_format": response_format
            }
            
            if language:
                kwargs["language"] = language
            
            if prompt:
                kwargs["prompt"] = prompt
            
            # Call OpenAI API
            response = openai_client.audio.transcriptions.create(**kwargs)
            
            if response_format == "json":
                text = response.text
                # OpenAI doesn't provide confidence scores, estimate based on model
                confidence = 0.95 if OPENAI_MODEL.startswith("gpt-4o") else 0.85
                detected_language = language or "auto"
            else:
                text = str(response)
                confidence = 0.95 if OPENAI_MODEL.startswith("gpt-4o") else 0.85
                detected_language = language or "auto"
            
            logger.info(f"OpenAI transcription completed. Model: {OPENAI_MODEL}, Length: {len(text)}")
            return text.strip(), confidence, detected_language
            
    except Exception as e:
        logger.error(f"OpenAI transcription failed: {str(e)}")
        raise


async def transcribe_audio_hybrid(
    audio_path: Path,
    detailed: bool = True,
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    use_openai_first: bool = True
) -> Tuple[str, float, str, str]:
    """
    Hybrid transcription using OpenAI API as primary and local Whisper as fallback.
    
    Args:
        audio_path: Path to the audio file
        detailed: Whether to perform detailed transcription (for authorized users)
        language: Target language code
        prompt: Context prompt for better transcription
        use_openai_first: Whether to try OpenAI first (True) or local first (False)
        
    Returns:
        Tuple[str, float, str, str]: Transcription text, confidence, language, source
    """
    errors = []
    
    if use_openai_first and openai_client:
        try:
            # Try OpenAI API first
            logger.info("Attempting transcription with OpenAI API...")
            text, confidence, detected_lang = await transcribe_with_openai(
                audio_path, language, prompt
            )
            
            # For unauthorized users, provide minimal output
            if not detailed:
                text = "Voice authentication required for full transcription"
                confidence = min(confidence, 0.5)
            
            return text, confidence, detected_lang, "openai"
            
        except Exception as e:
            error_msg = f"OpenAI transcription failed: {str(e)}"
            errors.append(error_msg)
            logger.warning(error_msg)
    
    # Fallback to local Whisper
    if FALLBACK_TO_LOCAL:
        try:
            logger.info("Falling back to local Whisper transcription...")
            text, confidence, detected_lang = await local_transcribe(audio_path, detailed)
            return text, confidence, detected_lang, "local"
            
        except Exception as e:
            error_msg = f"Local Whisper transcription failed: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
    
    # If all methods failed
    error_summary = "; ".join(errors)
    logger.error(f"All transcription methods failed: {error_summary}")
    return f"Transcription failed: {error_summary}", 0.0, "unknown", "failed"


async def translate_audio(
    audio_path: Path,
    target_language: str = "en",
    prompt: Optional[str] = None
) -> Tuple[str, float, str]:
    """
    Translate audio to target language using OpenAI API.
    
    Args:
        audio_path: Path to the audio file
        target_language: Target language code (default: "en" for English)
        prompt: Context prompt for better translation
        
    Returns:
        Tuple[str, float, str]: Translated text, confidence score, source language
    """
    if not openai_client:
        raise RuntimeError("OpenAI client not initialized for translation")
    
    try:
        with open(audio_path, "rb") as audio_file:
            kwargs = {
                "model": "whisper-1",  # Only whisper-1 supports translation
                "file": audio_file
            }
            
            if prompt:
                kwargs["prompt"] = prompt
            
            # Use translations endpoint for English translation
            response = openai_client.audio.translations.create(**kwargs)
            
            text = response.text.strip()
            confidence = 0.85  # Estimate for translation
            
            logger.info(f"Translation completed to {target_language}. Length: {len(text)}")
            return text, confidence, "auto"
            
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        raise


def get_openai_status() -> Dict[str, Any]:
    """
    Get status of OpenAI API integration.
    
    Returns:
        Dict with status information
    """
    return {
        "openai_available": openai_client is not None,
        "api_key_configured": bool(OPENAI_API_KEY),
        "model": OPENAI_MODEL,
        "fallback_enabled": FALLBACK_TO_LOCAL,
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024)
    }


async def chunk_large_audio(
    audio_path: Path, 
    chunk_size_mb: float = 20.0
) -> list[Path]:
    """
    Split large audio files into chunks for OpenAI API.
    
    Args:
        audio_path: Path to the audio file
        chunk_size_mb: Maximum chunk size in MB
        
    Returns:
        List of paths to audio chunks
    """
    try:
        from pydub import AudioSegment
        
        # Load audio
        audio = AudioSegment.from_file(str(audio_path))
        
        # Calculate chunk duration
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb <= chunk_size_mb:
            return [audio_path]  # No need to split
        
        # Calculate duration per chunk
        total_duration_ms = len(audio)
        chunk_duration_ms = int((chunk_size_mb / file_size_mb) * total_duration_ms)
        
        # Split into chunks
        chunks = []
        chunk_dir = audio_path.parent / f"{audio_path.stem}_chunks"
        chunk_dir.mkdir(exist_ok=True)
        
        for i, start_ms in enumerate(range(0, total_duration_ms, chunk_duration_ms)):
            end_ms = min(start_ms + chunk_duration_ms, total_duration_ms)
            chunk = audio[start_ms:end_ms]
            
            chunk_path = chunk_dir / f"chunk_{i:03d}{audio_path.suffix}"
            chunk.export(str(chunk_path), format=audio_path.suffix[1:])
            chunks.append(chunk_path)
        
        logger.info(f"Split audio into {len(chunks)} chunks")
        return chunks
        
    except ImportError:
        logger.error("pydub not available for audio chunking")
        raise RuntimeError("Audio chunking requires pydub package")
    except Exception as e:
        logger.error(f"Audio chunking failed: {str(e)}")
        raise


async def transcribe_large_audio(
    audio_path: Path,
    detailed: bool = True,
    language: Optional[str] = None,
    prompt: Optional[str] = None
) -> Tuple[str, float, str, str]:
    """
    Transcribe large audio files by chunking them.
    
    Args:
        audio_path: Path to the audio file
        detailed: Whether to perform detailed transcription
        language: Target language code
        prompt: Context prompt
        
    Returns:
        Tuple[str, float, str, str]: Combined transcription, avg confidence, language, source
    """
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    
    if file_size_mb <= 25:
        # Use normal transcription
        return await transcribe_audio_hybrid(audio_path, detailed, language, prompt)
    
    # Split and transcribe chunks
    chunks = await chunk_large_audio(audio_path)
    
    try:
        transcriptions = []
        confidences = []
        languages = []
        
        for i, chunk_path in enumerate(chunks):
            # Update prompt with context from previous chunks
            chunk_prompt = prompt
            if i > 0 and transcriptions:
                # Add context from previous chunk
                prev_text = transcriptions[-1].split()[-20:]  # Last 20 words
                chunk_prompt = f"{prompt or ''} Previous context: {' '.join(prev_text)}"
            
            text, conf, lang, source = await transcribe_audio_hybrid(
                chunk_path, detailed, language, chunk_prompt
            )
            
            transcriptions.append(text)
            confidences.append(conf)
            languages.append(lang)
        
        # Combine results
        combined_text = " ".join(transcriptions)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        primary_language = max(set(languages), key=languages.count) if languages else "unknown"
        
        return combined_text, avg_confidence, primary_language, "chunked"
        
    finally:
        # Cleanup chunks
        for chunk_path in chunks:
            try:
                chunk_path.unlink()
            except Exception:
                pass
        
        # Remove chunk directory if empty
        chunk_dir = chunks[0].parent if chunks else None
        if chunk_dir and chunk_dir.exists():
            try:
                chunk_dir.rmdir()
            except Exception:
                pass
