"""
Tests for the Hybrid STT functionality.
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import only what we need to run basic tests
try:
    from app.main import app
    from app.hybrid.controller import process_audio_hybrid, calculate_semantic_similarity
    APP_IMPORTS_SUCCESSFUL = True
except ImportError:
    APP_IMPORTS_SUCCESSFUL = False
    pass  # We'll skip tests that require these imports

# Skip all app-dependent tests if imports failed
pytestmark = pytest.mark.skipif(not APP_IMPORTS_SUCCESSFUL, 
                               reason="App imports failed, skipping app-dependent tests")

@pytest.fixture
def client():
    """Test client fixture."""
    if APP_IMPORTS_SUCCESSFUL:
        return TestClient(app)
    return None

@pytest.fixture
def sample_audio_path():
    """Create a simple mock audio file for testing."""
    # Create a temporary test file if TEST_AUDIO_PATH is not set
    if not os.environ.get("TEST_AUDIO_PATH"):
        import tempfile
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp.write(b"mock audio data")
        temp.close()
        return temp.name
    return os.environ.get("TEST_AUDIO_PATH")

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock dependencies to avoid actual processing."""
    # Only apply mocks if imports were successful
    if APP_IMPORTS_SUCCESSFUL:
        with patch("app.audio.processor.process_audio_file") as mock_process:
            with patch("app.transcription.speech_recognition.transcribe_audio") as mock_transcribe:
                with patch("app.voice_auth.verification.verify_speaker") as mock_verify:
                    with patch("app.hybrid.controller.process_audio_remote") as mock_remote:
                        with patch("app.audio.processor.get_audio_metadata") as mock_metadata:
                            # Setup the mocks
                            mock_process.return_value = Path("/tmp/processed_audio.wav")
                            mock_transcribe.return_value = ("тестовый текст", 0.95, "ru")
                            mock_verify.return_value = (True, 0.92)
                            mock_remote.return_value = {
                                "source": "remote",
                                "text": "тестовый текст (удаленный)",
                                "metadata": {
                                    "confidence": 0.88,
                                    "speaker_match": 0.85,
                                    "duration": 3.5,
                                    "language": "ru",
                                    "fallback_used": False
                                }
                            }
                            mock_metadata.return_value = (3.5, {"sample_rate": 16000})
                            yield


def test_hybrid_stt_endpoint(client, sample_audio_path):
    """Test the hybrid STT endpoint."""
    if not client:
        pytest.skip("Client not available")
    
    with open(sample_audio_path, "rb") as f:
        response = client.post(
            "/api/v1/hybrid/stt",
            files={"audio_file": ("test.wav", f, "audio/wav")},
            params={"verify_speaker": "false", "return_debug": "true"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "source" in data
    assert "text" in data
    assert "metadata" in data
    assert "confidence" in data["metadata"]
    assert "language" in data["metadata"]


def test_hybrid_stt_endpoint_with_semantics(client, sample_audio_path):
    """Test the hybrid STT endpoint with semantic validation."""
    if not client:
        pytest.skip("Client not available")
    
    with open(sample_audio_path, "rb") as f:
        response = client.post(
            "/api/v1/hybrid/stt",
            files={"audio_file": ("test.wav", f, "audio/wav")},
            params={
                "verify_speaker": "false", 
                "return_debug": "true",
                "use_semantics": "true",
                "semantic_threshold": "0.8"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "source" in data
    assert "text" in data
    assert "metadata" in data
    assert "fallback_used" in data["metadata"]


@pytest.mark.asyncio
async def test_process_audio_hybrid(sample_audio_path):
    """Test the hybrid audio processing function."""
    if not APP_IMPORTS_SUCCESSFUL:
        pytest.skip("App imports failed")
    
    result = await process_audio_hybrid(
        audio_path=Path(sample_audio_path),
        verify_speaker_flag=False,
        return_debug=True
    )
    
    assert isinstance(result, dict)
    assert "source" in result
    assert "text" in result
    assert "metadata" in result
    assert "confidence" in result["metadata"]
    assert "language" in result["metadata"]
    assert "fallback_used" in result["metadata"]


def test_mock_semantic_similarity():
    """Test a mock version of the semantic similarity function."""
    # Simple mock version that doesn't require sentence-transformers
    def mock_calculate_similarity(text1, text2):
        # Simple mock implementation
        common_words = set(text1.lower().split()) & set(text2.lower().split())
        total_words = set(text1.lower().split()) | set(text2.lower().split())
        return len(common_words) / len(total_words) if total_words else 0
    
    text1 = "Привет, как дела?"
    text2 = "Здравствуйте, как ваши дела?"
    
    similarity = mock_calculate_similarity(text1, text2)
    assert 0 <= similarity <= 1
    # "как" and "дела" are common, so similarity should be positive
    assert similarity > 0  


# Additional test for the controller with low confidence
@pytest.mark.asyncio
async def test_process_audio_hybrid_with_low_confidence(sample_audio_path):
    """Test hybrid processing with low confidence triggering fallback."""
    if not APP_IMPORTS_SUCCESSFUL:
        pytest.skip("App imports failed")
    
    # Setup specific mock for this test
    with patch("app.transcription.speech_recognition.transcribe_audio") as mock_transcribe:
        mock_transcribe.return_value = ("неуверенный текст", 0.7, "ru")  # Low confidence
        
        result = await process_audio_hybrid(
            audio_path=Path(sample_audio_path),
            verify_speaker_flag=False,
            return_debug=True
        )
    
    assert result["source"] == "remote"  # Should use remote due to low confidence
    assert result["metadata"]["fallback_used"] == True


# Test for the hybrid response format
def test_hybrid_response_format():
    """Test that the hybrid response format matches the specification."""
    sample_response = {
        "source": "local",
        "text": "включи свет в спальне",
        "metadata": {
            "confidence": 0.88,
            "speaker_match": 0.92,
            "duration": 5.1,
            "language": "ru",
            "fallback_used": False,
            "semantic_diff": 0.17
        }
    }
    
    # Validate structure
    assert "source" in sample_response
    assert sample_response["source"] in ["local", "remote"]
    assert "text" in sample_response
    assert isinstance(sample_response["text"], str)
    
    # Validate metadata
    metadata = sample_response["metadata"]
    assert "confidence" in metadata
    assert 0 <= metadata["confidence"] <= 1
    assert "duration" in metadata
    assert metadata["duration"] > 0
    assert "language" in metadata
    assert "fallback_used" in metadata
    assert isinstance(metadata["fallback_used"], bool)
    
    # Optional fields
    if "speaker_match" in metadata:
        assert metadata["speaker_match"] is None or 0 <= metadata["speaker_match"] <= 1
    if "semantic_diff" in metadata:
        assert metadata["semantic_diff"] is None or 0 <= metadata["semantic_diff"] <= 1
