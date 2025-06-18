"""
Hybrid Speech-to-Text controller for dynamic switching between OpenAI and local processing.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import torch
from app.utils.config import load_config
from app.audio.processor import process_audio_file, get_audio_metadata
from app.voice_auth.verification import verify_speaker
from app.transcription.openai_whisper import (
    transcribe_audio_hybrid, 
    transcribe_large_audio,
    get_openai_status,
    translate_audio
)

logger = logging.getLogger(__name__)

# Load configuration
config = load_config()
hybrid_config = config.get("hybrid_stt", {})
transcription_config = config.get("transcription", {})

# Configuration
PRIMARY_SERVICE = transcription_config.get("primary_service", "openai")
FALLBACK_TO_LOCAL = transcription_config.get("fallback_to_local", True)
MIN_CONFIDENCE = float(hybrid_config.get("min_confidence", 0.85))
MIN_SPEAKER_MATCH = float(hybrid_config.get("min_speaker_match", 0.90))
USE_SEMANTIC_VALIDATION = hybrid_config.get("use_semantic_validation", False)
SEMANTIC_MODEL = hybrid_config.get("semantic_model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
SEMANTIC_THRESHOLD = float(hybrid_config.get("semantic_threshold", 0.75))

# Initialize sentence transformer if semantic validation is enabled
sentence_transformer = None
if USE_SEMANTIC_VALIDATION:
    try:
        from sentence_transformers import SentenceTransformer
        sentence_transformer = SentenceTransformer(SEMANTIC_MODEL)
        logger.info(f"Sentence transformer model loaded: {SEMANTIC_MODEL}")
    except Exception as e:
        logger.warning(f"Failed to load sentence transformer: {str(e)}")
        USE_SEMANTIC_VALIDATION = False


async def process_audio_hybrid(
    audio_path: Path,
    verify_speaker_flag: bool = False,
    use_semantics: bool = False,
    semantic_threshold: float = 0.8,
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    return_debug: bool = False,
) -> Dict[str, Any]:
    """
    Process audio using hybrid approach (OpenAI API primary, local fallback).
    
    Args:
        audio_path: Path to the audio file
        verify_speaker_flag: Whether to perform speaker verification
        use_semantics: Whether to use semantic validation
        semantic_threshold: Threshold for semantic similarity
        language: Target language code
        prompt: Context prompt for better transcription
        return_debug: Whether to return debug information
        
    Returns:
        Dict with transcription results and metadata
    """
    try:
        # Get audio metadata
        metadata = get_audio_metadata(audio_path)
        audio_duration = metadata.get("duration", 0)
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        
        logger.info(f"Processing audio: {audio_path.name}, duration: {audio_duration:.2f}s, size: {file_size_mb:.2f}MB")
        
        # Initialize result structure
        result = {
            "source": "unknown",
            "text": "",
            "metadata": {
                "confidence": 0.0,
                "speaker_match": None,
                "duration": audio_duration,
                "language": "unknown",
                "file_size_mb": file_size_mb,
                "fallback_used": False,
                "semantic_diff": None
            }
        }
        
        # Perform speaker verification if requested
        speaker_verified = False
        speaker_confidence = 0.0
        
        if verify_speaker_flag:
            try:
                speaker_verified, speaker_confidence = await verify_speaker(audio_path)
                result["metadata"]["speaker_match"] = speaker_confidence
                
                if not speaker_verified:
                    logger.warning(f"Speaker verification failed: {speaker_confidence:.4f} < {MIN_SPEAKER_MATCH}")
                    if not return_debug:
                        result["text"] = "Speaker verification failed"
                        result["metadata"]["confidence"] = 0.0
                        result["source"] = "verification_failed"
                        return result
                        
            except Exception as e:
                logger.error(f"Speaker verification error: {str(e)}")
                result["metadata"]["speaker_match"] = 0.0
                if not return_debug:
                    result["text"] = "Speaker verification error"
                    result["source"] = "verification_error"
                    return result
        
        # Determine if user is authorized for detailed transcription
        authorized = not verify_speaker_flag or speaker_verified
        
        # Choose transcription method based on file size
        use_openai_first = PRIMARY_SERVICE == "openai"
        
        if file_size_mb > 25:
            # Use chunking for large files
            text, confidence, detected_language, source = await transcribe_large_audio(
                audio_path, authorized, language, prompt
            )
        else:
            # Use hybrid transcription
            text, confidence, detected_language, source = await transcribe_audio_hybrid(
                audio_path, authorized, language, prompt, use_openai_first
            )
        
        # Update result
        result["source"] = source
        result["text"] = text
        result["metadata"]["confidence"] = confidence
        result["metadata"]["language"] = detected_language
        result["metadata"]["fallback_used"] = source in ["local", "chunked"]
        
        # Semantic validation if enabled
        if use_semantics and sentence_transformer and source == "local" and authorized:
            try:
                # Get OpenAI result for comparison
                openai_text, openai_conf, openai_lang, _ = await transcribe_audio_hybrid(
                    audio_path, True, language, prompt, True
                )
                
                # Compare semantic similarity
                embeddings = sentence_transformer.encode([text, openai_text])
                similarity = float(torch.cosine_similarity(
                    torch.tensor(embeddings[0]).unsqueeze(0),
                    torch.tensor(embeddings[1]).unsqueeze(0)
                ))
                
                result["metadata"]["semantic_diff"] = 1.0 - similarity
                
                # Use OpenAI result if semantic difference is too high
                if similarity < semantic_threshold:
                    logger.info(f"Semantic validation failed: {similarity:.4f} < {semantic_threshold}, using OpenAI result")
                    result["text"] = openai_text
                    result["metadata"]["confidence"] = openai_conf
                    result["metadata"]["language"] = openai_lang
                    result["source"] = "openai_semantic"
                    
            except Exception as e:
                logger.warning(f"Semantic validation error: {str(e)}")
        
        # Add debug information if requested
        if return_debug:
            result["debug"] = {
                "openai_status": get_openai_status(),
                "primary_service": PRIMARY_SERVICE,
                "fallback_enabled": FALLBACK_TO_LOCAL,
                "semantic_validation": use_semantics,
                "file_info": {
                    "path": str(audio_path),
                    "size_mb": file_size_mb,
                    "duration": audio_duration,
                    "metadata": metadata
                }
            }
        
        logger.info(f"Transcription completed: source={source}, confidence={confidence:.4f}, length={len(text)}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        return {
            "source": "error",
            "text": f"Processing error: {str(e)}",
            "metadata": {
                "confidence": 0.0,
                "speaker_match": None,
                "duration": 0,
                "language": "unknown",
                "fallback_used": False,
                "semantic_diff": None
            }
        }


async def translate_audio_hybrid(
    audio_path: Path,
    target_language: str = "en",
    prompt: Optional[str] = None,
    return_debug: bool = False
) -> Dict[str, Any]:
    """
    Translate audio to target language using OpenAI API.
    
    Args:
        audio_path: Path to the audio file
        target_language: Target language code
        prompt: Context prompt for better translation
        return_debug: Whether to return debug information
        
    Returns:
        Dict with translation results and metadata
    """
    try:
        # Get audio metadata
        metadata = get_audio_metadata(audio_path)
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        
        # Translate using OpenAI API
        text, confidence, detected_language = await translate_audio(
            audio_path, target_language, prompt
        )
        
        result = {
            "source": "openai_translate",
            "text": text,
            "metadata": {
                "confidence": confidence,
                "source_language": detected_language,
                "target_language": target_language,
                "duration": metadata.get("duration", 0),
                "file_size_mb": file_size_mb
            }
        }
        
        if return_debug:
            result["debug"] = {
                "openai_status": get_openai_status(),
                "file_info": {
                    "path": str(audio_path),
                    "size_mb": file_size_mb,
                    "metadata": metadata
                }
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error translating audio: {str(e)}")
        return {
            "source": "error",
            "text": f"Translation error: {str(e)}",
            "metadata": {
                "confidence": 0.0,
                "source_language": "unknown",
                "target_language": target_language,
                "duration": 0,
                "file_size_mb": 0
            }
        }


def get_hybrid_status() -> Dict[str, Any]:
    """
    Get status of hybrid transcription system.
    
    Returns:
        Dict with system status information
    """
    return {
        "primary_service": PRIMARY_SERVICE,
        "fallback_enabled": FALLBACK_TO_LOCAL,
        "semantic_validation_enabled": USE_SEMANTIC_VALIDATION,
        "semantic_model": SEMANTIC_MODEL if sentence_transformer else None,
        "confidence_threshold": MIN_CONFIDENCE,
        "speaker_match_threshold": MIN_SPEAKER_MATCH,
        "openai_status": get_openai_status()
    }
