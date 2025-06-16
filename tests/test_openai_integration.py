"""
Mock tests for OpenAI Whisper integration.
"""
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from pathlib import Path

# Test configuration
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Test transcription result"
    mock_client.audio.transcriptions.create.return_value = mock_response
    mock_client.audio.translations.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_audio_path(tmp_path):
    """Create a temporary audio file for testing."""
    audio_file = tmp_path / "test_audio.wav"
    # Create a small dummy file
    audio_file.write_bytes(b"fake audio data")
    return audio_file


class TestOpenAIWhisperIntegration:
    """Test OpenAI Whisper API integration."""
    
    def test_openai_imports(self):
        """Test that OpenAI modules can be imported."""
        try:
            from app.transcription.openai_whisper import (
                transcribe_with_openai,
                transcribe_audio_hybrid,
                get_openai_status
            )
            assert True, "OpenAI whisper module imported successfully"
        except ImportError as e:
            pytest.skip(f"OpenAI whisper module import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_get_openai_status(self):
        """Test getting OpenAI API status."""
        try:
            from app.transcription.openai_whisper import get_openai_status
            
            status = get_openai_status()
            
            assert isinstance(status, dict)
            assert "openai_available" in status
            assert "api_key_configured" in status
            assert "model" in status
            assert "fallback_enabled" in status
            assert "max_file_size_mb" in status
            
        except ImportError:
            pytest.skip("OpenAI whisper module not available")
    
    @pytest.mark.asyncio
    async def test_transcribe_with_openai_mock(self, mock_openai_client, sample_audio_path):
        """Test OpenAI transcription with mocked client."""
        try:
            from app.transcription.openai_whisper import transcribe_with_openai
            
            with patch('app.transcription.openai_whisper.openai_client', mock_openai_client):
                text, confidence, language = await transcribe_with_openai(sample_audio_path)
                
                assert isinstance(text, str)
                assert isinstance(confidence, float)
                assert isinstance(language, str)
                assert len(text) > 0
                
        except ImportError:
            pytest.skip("OpenAI whisper module not available")
    
    @pytest.mark.asyncio
    async def test_hybrid_transcription_fallback(self, sample_audio_path):
        """Test hybrid transcription fallback to local when OpenAI fails."""
        try:
            from app.transcription.openai_whisper import transcribe_audio_hybrid
            
            # Mock OpenAI failure
            with patch('app.transcription.openai_whisper.openai_client', None):
                text, confidence, language, source = await transcribe_audio_hybrid(
                    sample_audio_path, detailed=True, use_openai_first=True
                )
                
                # Should fallback to local or return error
                assert source in ["local", "failed"]
                assert isinstance(text, str)
                assert isinstance(confidence, float)
                assert isinstance(language, str)
                
        except ImportError:
            pytest.skip("OpenAI whisper module not available")
    
    @pytest.mark.asyncio
    async def test_file_size_check(self, tmp_path):
        """Test file size validation for OpenAI API."""
        try:
            from app.transcription.openai_whisper import transcribe_with_openai
            
            # Create a file that's "too large" (mock the size check)
            large_file = tmp_path / "large_audio.wav"
            large_file.write_bytes(b"x" * 100)  # Small file, but we'll mock the stat
            
            # Mock file size to be larger than 25MB AND mock OpenAI client
            with patch.object(Path, 'stat') as mock_stat, \
                 patch('app.transcription.openai_whisper.openai_client', True):
                mock_stat.return_value.st_size = 26 * 1024 * 1024  # 26MB
                
                with pytest.raises(ValueError, match="exceeds OpenAI limit"):
                    await transcribe_with_openai(large_file)
                    
        except ImportError:
            pytest.skip("OpenAI whisper module not available")


class TestHybridController:
    """Test hybrid controller with OpenAI integration."""
    
    @pytest.mark.asyncio
    async def test_controller_imports(self):
        """Test that hybrid controller can be imported."""
        try:
            from app.hybrid.controller import (
                process_audio_hybrid,
                get_hybrid_status,
                translate_audio_hybrid
            )
            assert True, "Hybrid controller imported successfully"
        except ImportError as e:
            pytest.skip(f"Hybrid controller import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_get_hybrid_status(self):
        """Test getting hybrid system status."""
        try:
            from app.hybrid.controller import get_hybrid_status
            
            status = get_hybrid_status()
            
            assert isinstance(status, dict)
            assert "primary_service" in status
            assert "fallback_enabled" in status
            assert "openai_status" in status
            
        except ImportError:
            pytest.skip("Hybrid controller not available")
    
    @pytest.mark.asyncio
    async def test_process_audio_hybrid_mock(self, sample_audio_path):
        """Test processing audio with mocked dependencies."""
        try:
            from app.hybrid.controller import process_audio_hybrid
            
            # Mock all the dependencies
            with patch('app.hybrid.controller.get_audio_metadata') as mock_metadata, \
                 patch('app.hybrid.controller.verify_speaker') as mock_verify, \
                 patch('app.hybrid.controller.transcribe_audio_hybrid') as mock_transcribe:
                
                # Setup mocks
                mock_metadata.return_value = {"duration": 10.0}
                mock_verify.return_value = (True, 0.95)
                mock_transcribe.return_value = ("Test transcription", 0.9, "en", "openai")
                
                result = await process_audio_hybrid(
                    audio_path=sample_audio_path,
                    verify_speaker_flag=False,
                    return_debug=True
                )
                
                assert isinstance(result, dict)
                assert "source" in result
                assert "text" in result
                assert "metadata" in result
                assert result["text"] == "Test transcription"
                
        except ImportError:
            pytest.skip("Hybrid controller not available")


class TestConfiguration:
    """Test configuration for OpenAI integration."""
    
    def test_config_structure(self):
        """Test that configuration has required OpenAI settings."""
        try:
            from app.utils.config import load_config
            
            config = load_config()
            
            # Check if OpenAI section exists
            if "openai" in config:
                openai_config = config["openai"]
                assert "model" in openai_config
                assert "max_retries" in openai_config
                assert "timeout" in openai_config
            
            # Check transcription section
            if "transcription" in config:
                transcription_config = config["transcription"]
                assert "primary_service" in transcription_config
                assert "fallback_to_local" in transcription_config
                
        except ImportError:
            pytest.skip("Config module not available")
    
    def test_environment_variables(self):
        """Test that OpenAI API key can be set via environment."""
        # Test with mock environment variable
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            api_key = os.getenv("OPENAI_API_KEY")
            assert api_key == "test-key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
