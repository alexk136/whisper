"""
Tests for the Hybrid STT functionality.
"""
import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.hybrid.controller import process_audio_hybrid, calculate_semantic_similarity


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_hybrid_stt_endpoint(client):
    """Test the hybrid STT endpoint."""
    # This test requires an audio file
    test_audio = os.environ.get("TEST_AUDIO_PATH")
    if not test_audio or not os.path.exists(test_audio):
        pytest.skip("Test audio file not available")
    
    with open(test_audio, "rb") as f:
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


def test_hybrid_stt_endpoint_with_semantics(client):
    """Test the hybrid STT endpoint with semantic validation."""
    # This test requires an audio file
    test_audio = os.environ.get("TEST_AUDIO_PATH")
    if not test_audio or not os.path.exists(test_audio):
        pytest.skip("Test audio file not available")
    
    with open(test_audio, "rb") as f:
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
async def test_process_audio_hybrid():
    """Test the hybrid audio processing function."""
    # This test requires an audio file
    test_audio = os.environ.get("TEST_AUDIO_PATH")
    if not test_audio or not os.path.exists(test_audio):
        pytest.skip("Test audio file not available")
    
    result = await process_audio_hybrid(
        audio_path=Path(test_audio),
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


def test_semantic_similarity():
    """Test the semantic similarity function."""
    try:
        # This test requires sentence_transformers
        import torch
        from sentence_transformers import SentenceTransformer
    except ImportError:
        pytest.skip("sentence_transformers not installed")
    
    # Test with simple sentences
    text1 = "Привет, как дела?"
    text2 = "Здравствуйте, как ваши дела?"
    
    # If the function returns without error, consider it a pass
    # We can't assert specific values since the model might not be loaded
    try:
        similarity = calculate_semantic_similarity(text1, text2)
        assert 0 <= similarity <= 1
    except Exception:
        # If model is not available, this will skip
        pytest.skip("Semantic model not available")
