"""
Language Model integration module for the Whisper Voice Auth microservice.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from app.utils.config import load_config

logger = logging.getLogger(__name__)

# Load configuration
config = load_config()
LLM_API_URL = config.get("llm", {}).get("api_url", os.environ.get("WHISPER_LLM_API_URL"))
LLM_API_KEY = config.get("llm", {}).get("api_key", os.environ.get("WHISPER_LLM_API_KEY"))
LLM_TIMEOUT = config.get("llm", {}).get("timeout", 30)


async def process_command(transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a transcribed command with a language model.
    
    Args:
        transcript: Transcribed text to process
        metadata: Additional metadata about the audio
        
    Returns:
        Dict[str, Any]: LLM processing result
    """
    if not LLM_API_URL:
        logger.warning("LLM API URL not configured. Command processing skipped.")
        return {
            "success": False,
            "response": "Language model integration not configured",
            "action_taken": None,
        }
    
    try:
        # Prepare request to LLM API
        headers = {
            "Content-Type": "application/json",
        }
        
        # Add API key if provided
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"
        
        # Create payload
        payload = {
            "text": transcript,
            "metadata": metadata,
            "source": "whisper_voice_auth",
        }
        
        # Send request to LLM API
        response = requests.post(
            LLM_API_URL,
            headers=headers,
            json=payload,
            timeout=LLM_TIMEOUT,
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Command processed successfully: {result.get('response')}")
            return {
                "success": True,
                "response": result.get("response", "Command processed"),
                "action_taken": result.get("action"),
                "details": result.get("details"),
            }
        else:
            logger.error(f"LLM API error: {response.status_code} - {response.text}")
            return {
                "success": False,
                "response": f"Error processing command: {response.status_code}",
                "action_taken": None,
            }
    
    except Exception as e:
        logger.error(f"Error processing command with LLM: {str(e)}")
        return {
            "success": False,
            "response": f"Error processing command: {str(e)}",
            "action_taken": None,
        }
