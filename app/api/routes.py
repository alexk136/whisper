"""
API routes for the Whisper Voice Auth microservice.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging

from app.api.schemas import VerificationResponse, ErrorResponse
from app.audio.processor import process_audio_file
from app.voice_auth.verification import verify_speaker
from app.transcription.speech_recognition import transcribe_audio
from app.llm.integration import process_command
from app.utils.security import validate_api_key

logger = logging.getLogger(__name__)

# Create router
api_router = APIRouter()


@api_router.post(
    "/voice/verify",
    response_model=VerificationResponse,
    responses={
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
    description="Upload an audio file for voice verification and processing.",
)
async def voice_verify(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    audio_url: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    api_key: str = Depends(validate_api_key),
) -> VerificationResponse:
    """
    Verify the voice in an audio file and process the spoken command if authorized.
    
    Args:
        background_tasks: FastAPI background tasks
        audio_file: Uploaded audio file (WAV, MP3, etc.)
        audio_url: URL to audio file (alternative to upload)
        authorization: Bearer token (optional)
        api_key: API key for service authentication
        
    Returns:
        VerificationResponse: The verification result with transcript and metadata
    """
    try:
        # Process and normalize the audio file
        processed_audio_path = await process_audio_file(audio_file, audio_url)
        
        # Verify the speaker
        speaker_verified, speaker_match_score = await verify_speaker(processed_audio_path)
        
        # Transcribe the audio (different levels based on verification)
        transcript, confidence, language = await transcribe_audio(
            processed_audio_path, 
            detailed=speaker_verified
        )
        
        # Prepare metadata
        audio_metadata = {
            "confidence": confidence,
            "speaker_match": speaker_match_score,
            "language": language,
            # Additional metadata will be added by the processor
        }
        
        # Process the command with LLM if speaker is verified
        if speaker_verified:
            # Schedule background task to process with LLM
            background_tasks.add_task(
                process_command,
                transcript=transcript,
                metadata=audio_metadata
            )
            
            status = "AUTHORIZED"
        else:
            status = "UNAUTHORIZED"
            # Obfuscate transcript for unauthorized users
            if transcript:
                transcript = "Unauthorized access. Voice verification failed."
        
        # Return response
        return VerificationResponse(
            status=status,
            text=transcript,
            metadata=audio_metadata
        )
        
    except Exception as e:
        logger.error(f"Error processing voice verification: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error processing audio: {str(e)}"
        )


@api_router.post(
    "/voice/register",
    response_model=Dict[str, Any],
    description="Register a new voice print for the owner.",
)
async def register_voice(
    audio_files: List[UploadFile] = File(...),
    api_key: str = Depends(validate_api_key),
) -> Dict[str, Any]:
    """
    Register a new voice print from audio samples.
    
    Args:
        audio_files: List of audio files containing the owner's voice
        api_key: API key for service authentication
        
    Returns:
        Dict[str, Any]: Result of voice registration
    """
    try:
        # Process each audio file
        processed_paths = []
        for audio_file in audio_files:
            processed_path = await process_audio_file(audio_file)
            processed_paths.append(processed_path)
        
        # Create and store voice print
        from app.voice_auth.registration import register_voice_print
        success, voice_id = await register_voice_print(processed_paths)
        
        if not success:
            raise HTTPException(
                status_code=422,
                detail="Failed to register voice print. Ensure audio quality is good."
            )
        
        return {
            "status": "success",
            "message": "Voice print registered successfully",
            "voice_id": voice_id
        }
        
    except Exception as e:
        logger.error(f"Error registering voice: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error registering voice: {str(e)}"
        )
