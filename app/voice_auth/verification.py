"""
Speaker verification module for the Whisper Voice Auth microservice.
"""
import os
import pickle
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional
import torch
from resemblyzer import VoiceEncoder, preprocess_wav
from app.utils.config import load_config

logger = logging.getLogger(__name__)

# Load configuration
config = load_config()
VERIFICATION_THRESHOLD = config.get("auth", {}).get("speaker_verification_threshold", 0.75)

# Path to stored voice prints
VOICEPRINT_DIR = Path(os.environ.get("WHISPER_VOICEPRINT_DIR", "app/storage/voiceprints"))
VOICEPRINT_DIR.mkdir(parents=True, exist_ok=True)

# Initialize voice encoder
try:
    voice_encoder = VoiceEncoder()
    logger.info("Voice encoder initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize voice encoder: {str(e)}")
    voice_encoder = None


def get_voice_embedding(audio_path: Path) -> np.ndarray:
    """
    Extract voice embedding from audio file.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        np.ndarray: Voice embedding vector
    """
    if voice_encoder is None:
        raise RuntimeError("Voice encoder not initialized")
    
    # Preprocess WAV file for the encoder
    wav = preprocess_wav(str(audio_path))
    
    # Extract embedding
    embedding = voice_encoder.embed_utterance(wav)
    return embedding


async def verify_speaker(audio_path: Path) -> Tuple[bool, float]:
    """
    Verify if the speaker in the audio matches the stored voiceprint.
    
    Args:
        audio_path: Path to the audio file to verify
        
    Returns:
        Tuple[bool, float]: Verification result (True if verified) and similarity score
    """
    try:
        # Get the voiceprint
        owner_voiceprint = load_owner_voiceprint()
        if owner_voiceprint is None:
            logger.warning("No owner voiceprint found. Verification failed.")
            return False, 0.0
        
        # Extract embedding from the input audio
        new_embedding = get_voice_embedding(audio_path)
        
        # Calculate similarity score
        similarity = cosine_similarity(new_embedding, owner_voiceprint)
        
        # Check if the score is above the threshold
        is_verified = similarity >= VERIFICATION_THRESHOLD
        
        logger.info(f"Voice verification result: {is_verified}, score: {similarity:.4f}")
        return is_verified, float(similarity)
    
    except Exception as e:
        logger.error(f"Error during speaker verification: {str(e)}")
        return False, 0.0


def load_owner_voiceprint() -> Optional[np.ndarray]:
    """
    Load the owner's voiceprint from storage.
    
    Returns:
        Optional[np.ndarray]: Owner's voiceprint embedding or None if not found
    """
    voiceprint_path = VOICEPRINT_DIR / "owner_voiceprint.pkl"
    
    if not voiceprint_path.exists():
        return None
    
    try:
        with open(voiceprint_path, "rb") as f:
            # In production, this should be decrypted using app.utils.security.decrypt_data
            voiceprint = pickle.load(f)
        return voiceprint
    except Exception as e:
        logger.error(f"Error loading owner voiceprint: {str(e)}")
        return None


def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        float: Cosine similarity score (0-1)
    """
    # Normalize the embeddings
    embedding1 = embedding1 / np.linalg.norm(embedding1)
    embedding2 = embedding2 / np.linalg.norm(embedding2)
    
    # Calculate cosine similarity
    similarity = np.dot(embedding1, embedding2)
    
    return similarity
