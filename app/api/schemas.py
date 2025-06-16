"""
API schemas for the Whisper Voice Auth microservice.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str = Field(..., description="Error detail message")


class VerificationResponse(BaseModel):
    """Voice verification response schema."""
    status: str = Field(..., description="Authentication status: AUTHORIZED or UNAUTHORIZED")
    text: str = Field(..., description="Transcribed text from the audio")
    metadata: Dict[str, Any] = Field(
        ...,
        description="Metadata about the verification process and audio"
    )


class AudioMetadata(BaseModel):
    """Audio metadata schema."""
    confidence: float = Field(..., description="Confidence score of the transcription")
    speaker_match: Optional[float] = Field(None, description="Voice similarity score with the owner")
    duration: Optional[float] = Field(None, description="Duration of the audio in seconds")
    language: Optional[str] = Field(None, description="Detected language of the speech")
    sample_rate: Optional[int] = Field(None, description="Sample rate of the processed audio")
    format: Optional[str] = Field(None, description="Format of the original audio file")


class CommandRequest(BaseModel):
    """Command processing request schema."""
    text: str = Field(..., description="Transcribed text to process as a command")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CommandResponse(BaseModel):
    """Command processing response schema."""
    success: bool = Field(..., description="Whether the command was processed successfully")
    response: str = Field(..., description="Response to the command")
    action_taken: Optional[str] = Field(None, description="Action taken in response to the command")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the command processing")


class HybridSTTMetadata(BaseModel):
    """Hybrid STT metadata schema."""
    confidence: float = Field(..., description="Confidence score of the transcription")
    speaker_match: Optional[float] = Field(None, description="Voice similarity score with the owner")
    duration: float = Field(..., description="Duration of the audio in seconds")
    language: str = Field(..., description="Detected language of the speech")
    fallback_used: bool = Field(..., description="Whether the fallback to remote API was used")
    semantic_diff: Optional[float] = Field(None, description="Semantic difference between local and remote results")


class HybridSTTResponse(BaseModel):
    """Hybrid STT response schema."""
    source: str = Field(..., description="Source of the transcription: 'local' or 'remote'")
    text: str = Field(..., description="Transcribed text from the audio")
    metadata: HybridSTTMetadata = Field(..., description="Metadata about the STT process")
