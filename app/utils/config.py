"""
Configuration utilities for the Whisper Voice Auth microservice.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config.yaml")
ENV_CONFIG_PATH = os.environ.get("CONFIG_PATH")


def load_config() -> Dict[str, Any]:
    """
    Load configuration from a YAML file and environment variables.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = {}
    
    # Determine config path
    config_path = Path(ENV_CONFIG_PATH) if ENV_CONFIG_PATH else DEFAULT_CONFIG_PATH
    
    # Load from YAML file if it exists
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
    else:
        logger.warning(f"Configuration file {config_path} not found. Using defaults and environment variables.")
    
    # Override with environment variables
    # Format: WHISPER_SECTION_KEY=value (e.g., WHISPER_API_SECRET_KEY=mysecret)
    for env_key, env_value in os.environ.items():
        if env_key.startswith("WHISPER_"):
            parts = env_key.lower().split("_", 2)[1:]  # Remove WHISPER_ prefix and split
            
            if len(parts) == 1:
                # Single level: WHISPER_KEY=value
                config[parts[0]] = _parse_env_value(env_value)
            elif len(parts) == 2:
                # Two levels: WHISPER_SECTION_KEY=value
                section, key = parts
                if section not in config:
                    config[section] = {}
                config[section][key] = _parse_env_value(env_value)
    
    # Set defaults if not provided
    config.setdefault("development_mode", False)
    config.setdefault("cors", {}).setdefault("origins", ["*"])
    config.setdefault("auth", {}).setdefault("speaker_verification_threshold", 0.75)
    
    return config


def _parse_env_value(value: str) -> Any:
    """
    Parse environment variable values to appropriate Python types.
    
    Args:
        value (str): The string value from an environment variable
        
    Returns:
        Any: Parsed value (bool, int, float, or str)
    """
    # Convert "true"/"false" to boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    
    # Try to convert to integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Try to convert to float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Keep as string
    return value
