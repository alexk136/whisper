"""
Audio processing utilities for the Whisper Voice Auth microservice.
"""
import os
import uuid
import tempfile
from pathlib import Path
import logging
import aiofiles
import aiohttp
from fastapi import UploadFile
from typing import Optional, Tuple, Dict, Any
import ffmpeg
import librosa
import soundfile as sf
from pydub import AudioSegment

logger = logging.getLogger(__name__)

# Define constants
ALLOWED_AUDIO_FORMATS = [".wav", ".mp3", ".m4a", ".ogg", ".flac"]
TARGET_SAMPLE_RATE = 16000  # 16kHz, standard for most speech recognition models
TARGET_CHANNELS = 1  # Mono
TEMP_DIR = Path(tempfile.gettempdir()) / "whisper_audio"
STORAGE_DIR = Path(os.environ.get("WHISPER_STORAGE_DIR", "app/storage/audio"))


# Ensure directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


async def process_audio_file(
    audio_file: Optional[UploadFile] = None,
    audio_url: Optional[str] = None,
) -> Path:
    """
    Process and normalize an audio file from upload or URL.
    
    Args:
        audio_file: Uploaded audio file
        audio_url: URL to audio file
        
    Returns:
        Path: Path to the processed audio file
        
    Raises:
        ValueError: If neither audio_file nor audio_url is provided
    """
    if not audio_file and not audio_url:
        raise ValueError("Either audio_file or audio_url must be provided")
    
    # Generate unique filename
    temp_id = str(uuid.uuid4())
    
    # Save the original file
    if audio_file:
        # Get file extension
        file_ext = Path(audio_file.filename).suffix.lower()
        if file_ext not in ALLOWED_AUDIO_FORMATS:
            raise ValueError(f"Unsupported audio format: {file_ext}. Supported formats: {', '.join(ALLOWED_AUDIO_FORMATS)}")
        
        # Save uploaded file
        orig_path = TEMP_DIR / f"original_{temp_id}{file_ext}"
        async with aiofiles.open(orig_path, "wb") as f:
            content = await audio_file.read()
            await f.write(content)
    else:
        # Download from URL
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download audio from URL: {response.status}")
                
                # Determine file extension from content-type or URL
                content_type = response.headers.get("Content-Type", "")
                if "audio/wav" in content_type or audio_url.endswith(".wav"):
                    file_ext = ".wav"
                elif "audio/mp3" in content_type or audio_url.endswith(".mp3"):
                    file_ext = ".mp3"
                elif "audio/m4a" in content_type or audio_url.endswith(".m4a"):
                    file_ext = ".m4a"
                elif "audio/ogg" in content_type or audio_url.endswith(".ogg"):
                    file_ext = ".ogg"
                elif "audio/flac" in content_type or audio_url.endswith(".flac"):
                    file_ext = ".flac"
                else:
                    raise ValueError(f"Unsupported audio format from URL: {content_type}")
                
                orig_path = TEMP_DIR / f"original_{temp_id}{file_ext}"
                async with aiofiles.open(orig_path, "wb") as f:
                    await f.write(await response.read())
    
    logger.info(f"Saved original audio to {orig_path}")
    
    # Normalize and convert the audio
    processed_path = TEMP_DIR / f"processed_{temp_id}.wav"
    
    try:
        # Convert to WAV with proper settings
        await normalize_audio(orig_path, processed_path)
        
        # Get audio metadata
        duration, _ = get_audio_metadata(processed_path)
        
        # Validate duration
        if duration < 2 or duration > 20:
            raise ValueError(f"Audio duration must be between 2 and 20 seconds. Got: {duration:.2f} seconds")
        
        logger.info(f"Processed audio saved to {processed_path}")
        return processed_path
    
    except Exception as e:
        logger.error(f"Error processing audio file: {str(e)}")
        # Clean up files
        if orig_path.exists():
            orig_path.unlink()
        if processed_path.exists():
            processed_path.unlink()
        raise


async def normalize_audio(input_path: Path, output_path: Path) -> None:
    """
    Normalize audio to standard format for processing.
    
    Args:
        input_path: Path to input audio file
        output_path: Path to save normalized audio
        
    Raises:
        RuntimeError: If audio processing fails
    """
    try:
        # Use ffmpeg to normalize audio
        (
            ffmpeg
            .input(str(input_path))
            .output(
                str(output_path),
                acodec='pcm_s16le',  # 16-bit PCM
                ar=TARGET_SAMPLE_RATE,  # Sample rate
                ac=TARGET_CHANNELS,  # Mono
                loglevel='error'
            )
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        raise RuntimeError(f"Failed to process audio: {e.stderr.decode() if e.stderr else str(e)}")


def get_audio_metadata(audio_path: Path) -> Tuple[float, Dict[str, Any]]:
    """
    Get metadata from an audio file.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Tuple[float, Dict[str, Any]]: Duration and metadata dictionary
    """
    # Load audio file
    y, sr = librosa.load(audio_path, sr=None)
    
    # Calculate duration
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Get other metadata
    metadata = {
        "sample_rate": sr,
        "channels": 1 if y.ndim == 1 else y.shape[0],
        "duration": duration,
        "format": audio_path.suffix[1:],  # Remove dot from extension
    }
    
    return duration, metadata
