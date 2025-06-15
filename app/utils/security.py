"""
Security utilities for the Whisper Voice Auth microservice.
"""
import os
import logging
from fastapi import HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
from app.utils.config import load_config

logger = logging.getLogger(__name__)

# API Key security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Load configuration
config = load_config()


async def validate_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
) -> str:
    """
    Validate the API key provided in the request header.
    
    Args:
        api_key_header: API key from the request header
        
    Returns:
        str: The valid API key
        
    Raises:
        HTTPException: If the API key is invalid or missing
    """
    # Get valid API keys from config or environment
    valid_api_keys = config.get("api", {}).get("keys", [])
    
    # Add API key from environment if available
    env_api_key = os.environ.get("WHISPER_API_KEY")
    if env_api_key:
        valid_api_keys.append(env_api_key)
    
    # Skip validation in development mode if configured
    if config.get("development_mode", False) and config.get("skip_api_validation", False):
        return api_key_header or "dev_mode"
    
    # Validate the API key
    if not api_key_header or api_key_header not in valid_api_keys:
        logger.warning("Invalid or missing API key")
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key",
        )
    
    return api_key_header


def encrypt_data(data: bytes) -> bytes:
    """
    Encrypt sensitive data for storage.
    
    Args:
        data: Data to encrypt
        
    Returns:
        bytes: Encrypted data
    """
    # Implementation using cryptography library
    # This is a placeholder and should be properly implemented with:
    # - Key management (from secure storage)
    # - Proper encryption algorithm (e.g., AES-256-GCM)
    # - Nonce/IV handling
    from cryptography.fernet import Fernet
    
    # In production, the key should be securely stored and retrieved
    key = os.environ.get("WHISPER_ENCRYPTION_KEY")
    if not key:
        # Generate a key if not available (this is just for development)
        # In production, you should have a consistent key management strategy
        key = Fernet.generate_key()
        logger.warning("Generated temporary encryption key - this should be properly configured")
    
    f = Fernet(key)
    return f.encrypt(data)


def decrypt_data(encrypted_data: bytes) -> bytes:
    """
    Decrypt stored sensitive data.
    
    Args:
        encrypted_data: Encrypted data to decrypt
        
    Returns:
        bytes: Decrypted data
    """
    # Implementation using cryptography library
    from cryptography.fernet import Fernet
    
    key = os.environ.get("WHISPER_ENCRYPTION_KEY")
    if not key:
        raise ValueError("Encryption key not available")
    
    f = Fernet(key)
    return f.decrypt(encrypted_data)
