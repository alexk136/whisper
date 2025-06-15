"""
Voice print registration module for the Whisper Voice Auth microservice.
"""
import os
import uuid
import pickle
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, List
from app.voice_auth.verification import get_voice_embedding, VOICEPRINT_DIR
from app.utils.security import encrypt_data

logger = logging.getLogger(__name__)


async def register_voice_print(audio_paths: List[Path]) -> Tuple[bool, str]:
    """
    Register a new voice print from multiple audio samples.
    
    Args:
        audio_paths: List of paths to audio files containing the owner's voice
        
    Returns:
        Tuple[bool, str]: Success status and voice ID
    """
    try:
        if not audio_paths:
            raise ValueError("No audio files provided for voice registration")
        
        # Extract embeddings from all audio files
        embeddings = []
        for audio_path in audio_paths:
            embedding = get_voice_embedding(audio_path)
            embeddings.append(embedding)
        
        # Create average embedding as the voiceprint
        voiceprint = np.mean(embeddings, axis=0)
        
        # Generate a unique ID for this voiceprint
        voice_id = str(uuid.uuid4())
        
        # Save the voiceprint
        await save_voice_print(voiceprint, "owner")
        
        logger.info(f"Voice print registered successfully with ID: {voice_id}")
        return True, voice_id
    
    except Exception as e:
        logger.error(f"Error registering voice print: {str(e)}")
        return False, ""


async def save_voice_print(voiceprint: np.ndarray, user_id: str) -> bool:
    """
    Save a voice print to storage.
    
    Args:
        voiceprint: The voice embedding to save
        user_id: User identifier (use "owner" for the main owner)
        
    Returns:
        bool: Success status
    """
    try:
        # Ensure directory exists
        VOICEPRINT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Define path for the voiceprint
        if user_id == "owner":
            voiceprint_path = VOICEPRINT_DIR / "owner_voiceprint.pkl"
        else:
            voiceprint_path = VOICEPRINT_DIR / f"{user_id}_voiceprint.pkl"
        
        # In production, encrypt the voiceprint
        # serialized = pickle.dumps(voiceprint)
        # encrypted_data = encrypt_data(serialized)
        # with open(voiceprint_path, "wb") as f:
        #     f.write(encrypted_data)
        
        # For development, save without encryption
        with open(voiceprint_path, "wb") as f:
            pickle.dump(voiceprint, f)
        
        logger.info(f"Saved voice print for user {user_id} at {voiceprint_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving voice print: {str(e)}")
        return False
