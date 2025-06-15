"""
Hybrid Speech-to-Text controller for dynamic switching between local and remote processing.
"""
import os
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import torch
from app.utils.config import load_config
from app.audio.processor import process_audio_file, get_audio_metadata
from app.voice_auth.verification import verify_speaker
from app.transcription.speech_recognition import transcribe_audio

logger = logging.getLogger(__name__)

# Load configuration
config = load_config().get("hybrid_stt", {})

# Default configuration
WHISPER_URL = config.get("whisper_url", "http://localhost:8000")
REMOTE_API_URL = config.get("remote_api_url", os.environ.get("REMOTE_API_URL", ""))
MIN_CONFIDENCE = float(config.get("min_confidence", 0.85))
MIN_SPEAKER_MATCH = float(config.get("min_speaker_match", 0.90))
TIMEOUT_LOCAL = int(config.get("timeout_local", 5))
USE_SEMANTIC_VALIDATION = config.get("use_semantic_validation", False)
SEMANTIC_MODEL = config.get("semantic_model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
SEMANTIC_THRESHOLD = float(config.get("semantic_threshold", 0.75))

# Initialize sentence transformer if semantic validation is enabled
sentence_transformer = None
if USE_SEMANTIC_VALIDATION or os.environ.get("WHISPER_HYBRID_STT_USE_SEMANTIC_VALIDATION", "").lower() == "true":
    USE_SEMANTIC_VALIDATION = True
    try:
        from sentence_transformers import SentenceTransformer
        model_name = SEMANTIC_MODEL
        sentence_transformer = SentenceTransformer(model_name)
        logger.info(f"Sentence transformer model loaded: {model_name}")
    except Exception as e:
        logger.warning(f"Failed to load sentence transformer: {str(e)}")
        USE_SEMANTIC_VALIDATION = False


async def process_audio_hybrid(
    audio_path: Path,
    verify_speaker_flag: bool = False,
    return_debug: bool = False,
) -> Dict[str, Any]:
    """
    Process audio using hybrid approach (local first, remote fallback).
    
    Args:
        audio_path: Path to processed audio file
        verify_speaker_flag: Whether to verify the speaker
        return_debug: Whether to return additional debug information
        
    Returns:
        Dict[str, Any]: Processing result with text and metadata
    """
    # Update config from environment variables if set
    semantic_threshold = os.environ.get("WHISPER_HYBRID_STT_SEMANTIC_THRESHOLD")
    semantic_threshold_value = SEMANTIC_THRESHOLD
    if semantic_threshold:
        try:
            semantic_threshold_value = float(semantic_threshold)
        except ValueError:
            logger.warning(f"Invalid semantic threshold value: {semantic_threshold}")
    
    result = {
        "source": "local",
        "text": "",
        "metadata": {
            "confidence": 0.0,
            "speaker_match": 0.0 if verify_speaker_flag else None,
            "duration": 0.0,
            "language": "",
            "fallback_used": False,
            "semantic_diff": None
        }
    }
    
    # Get audio metadata
    duration, audio_meta = get_audio_metadata(audio_path)
    result["metadata"]["duration"] = duration
    
    # Step 1: Process with local Whisper model
    try:
        # Verify speaker if needed
        speaker_match = 0.0
        if verify_speaker_flag:
            is_verified, speaker_match = await verify_speaker(audio_path)
            result["metadata"]["speaker_match"] = speaker_match
        
        # Transcribe audio
        text, confidence, language = await transcribe_audio(
            audio_path, 
            detailed=True  # Always get detailed transcription for hybrid processing
        )
        
        result["text"] = text
        result["metadata"]["confidence"] = confidence
        result["metadata"]["language"] = language
        
        # Step 2: Check if we need to use remote fallback
        use_fallback = False
        
        # Check confidence threshold
        if confidence < MIN_CONFIDENCE:
            logger.info(f"Low confidence ({confidence} < {MIN_CONFIDENCE}), using remote fallback")
            use_fallback = True
        
        # Check speaker match threshold if verification is enabled
        if verify_speaker_flag and speaker_match < MIN_SPEAKER_MATCH:
            logger.info(f"Low speaker match ({speaker_match} < {MIN_SPEAKER_MATCH}), using remote fallback")
            use_fallback = True
        
        # Step 3: Use remote fallback if needed
        if use_fallback and REMOTE_API_URL:
            remote_result = await process_audio_remote(audio_path, verify_speaker_flag)
            
            if remote_result:
                # Compare results semantically if enabled
                if USE_SEMANTIC_VALIDATION and sentence_transformer and text and remote_result["text"]:
                    semantic_diff = calculate_semantic_similarity(text, remote_result["text"])
                    result["metadata"]["semantic_diff"] = semantic_diff
                    
                    # Choose better result based on confidence and semantic similarity
                    if remote_result["metadata"]["confidence"] > confidence:
                        # If semantic similarity is high, prefer local result
                        if semantic_diff >= semantic_threshold_value and confidence >= 0.7:
                            logger.info(f"Using local result despite lower confidence due to high semantic similarity ({semantic_diff})")
                            # Keep local result but update metadata
                            result["metadata"]["fallback_used"] = False
                        else:
                            # Use remote result
                            result = remote_result
                            result["metadata"]["fallback_used"] = True
                            result["metadata"]["semantic_diff"] = semantic_diff
                    else:
                        # Keep local result but update metadata
                        result["metadata"]["fallback_used"] = False
                else:
                    # Simply use remote result if it has higher confidence
                    if remote_result["metadata"]["confidence"] > confidence:
                        result = remote_result
                        result["metadata"]["fallback_used"] = True
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing audio locally: {str(e)}")
        
        # Try remote processing as fallback for error
        if REMOTE_API_URL:
            try:
                remote_result = await process_audio_remote(audio_path, verify_speaker_flag)
                if remote_result:
                    remote_result["metadata"]["fallback_used"] = True
                    return remote_result
            except Exception as remote_e:
                logger.error(f"Error processing audio remotely: {str(remote_e)}")
        
        # Return error result if both methods fail
        result["text"] = "Error processing audio"
        result["metadata"]["confidence"] = 0.0
        return result


async def process_audio_remote(
    audio_path: Path,
    verify_speaker: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Process audio using remote API.
    
    Args:
        audio_path: Path to processed audio file
        verify_speaker: Whether to verify the speaker
        
    Returns:
        Optional[Dict[str, Any]]: Processing result with text and metadata
    """
    if not REMOTE_API_URL:
        logger.warning("Remote API URL not configured, cannot use remote processing")
        return None
    
    try:
        # Prepare the request
        files = {
            'audio_file': (audio_path.name, open(audio_path, 'rb'), 'audio/wav')
        }
        
        params = {
            'verify_speaker': str(verify_speaker).lower()
        }
        
        # Send request to remote API
        response = requests.post(
            REMOTE_API_URL,
            files=files,
            params=params,
            timeout=10  # Use longer timeout for remote API
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            
            # Format result to match our expected structure
            formatted_result = {
                "source": "remote",
                "text": result.get("text", ""),
                "metadata": {
                    "confidence": result.get("confidence", 0.0),
                    "speaker_match": result.get("speaker_match", None),
                    "duration": result.get("duration", 0.0),
                    "language": result.get("language", ""),
                    "fallback_used": False,
                    "semantic_diff": None
                }
            }
            
            return formatted_result
        else:
            logger.error(f"Remote API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error calling remote STT API: {str(e)}")
        return None


def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        float: Semantic similarity score (0-1)
    """
    if not sentence_transformer:
        return 0.0
    
    # Get embeddings
    embedding1 = sentence_transformer.encode(text1, convert_to_tensor=True)
    embedding2 = sentence_transformer.encode(text2, convert_to_tensor=True)
    
    # Calculate cosine similarity
    similarity = torch.nn.functional.cosine_similarity(embedding1.unsqueeze(0), embedding2.unsqueeze(0))
    
    return float(similarity.item())
