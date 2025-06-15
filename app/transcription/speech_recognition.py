"""
Speech recognition module for the Whisper Voice Auth microservice.
"""
import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import torch
import whisper
from app.utils.config import load_config

logger = logging.getLogger(__name__)

# Load configuration
config = load_config()
WHISPER_MODEL = config.get("transcription", {}).get("whisper_model", "base")
LANGUAGE = config.get("transcription", {}).get("language", None)  # None for auto-detection

# Initialize Whisper model
try:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    whisper_model = whisper.load_model(WHISPER_MODEL, device=device)
    logger.info(f"Whisper model '{WHISPER_MODEL}' loaded on {device}")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {str(e)}")
    whisper_model = None


async def transcribe_audio(
    audio_path: Path,
    detailed: bool = True,
) -> Tuple[str, float, str]:
    """
    Transcribe speech in audio file.
    
    Args:
        audio_path: Path to the audio file
        detailed: Whether to perform detailed transcription (for authorized users)
        
    Returns:
        Tuple[str, float, str]: Transcription text, confidence score, and detected language
    """
    if whisper_model is None:
        raise RuntimeError("Whisper model not initialized")
    
    try:
        # Set transcription options
        options = {
            "language": LANGUAGE,  # Can be None for auto-detection
            "task": "transcribe",
            "fp16": torch.cuda.is_available(),
        }
        
        # Process audio with Whisper
        result = whisper_model.transcribe(str(audio_path), **options)
        
        # Extract results
        text = result["text"].strip()
        language = result.get("language", "unknown")
        
        # Calculate average confidence
        segments = result.get("segments", [])
        if segments:
            confidence = sum(segment.get("confidence", 0) for segment in segments) / len(segments)
        else:
            confidence = 0.0
        
        # For unauthorized users, provide minimal output
        if not detailed:
            # Only return minimal info for security
            text = "Voice authentication required for full transcription"
            confidence = min(confidence, 0.5)  # Cap confidence for security
        
        logger.info(f"Transcription completed. Language: {language}, Confidence: {confidence:.4f}")
        return text, confidence, language
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return "Error during transcription", 0.0, "unknown"


def get_supported_languages() -> Dict[str, str]:
    """
    Get a dictionary of languages supported by the Whisper model.
    
    Returns:
        Dict[str, str]: Dictionary mapping language codes to language names
    """
    return whisper.tokenizer.LANGUAGES
