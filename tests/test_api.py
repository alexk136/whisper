"""
Tests for the Whisper Voice Auth microservice.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    result = response.json()
    # Check that health check returns proper structure
    assert "status" in result
    assert result["status"] in ["healthy", "ok"]
    # If it's the new format, check for components
    if result["status"] == "healthy":
        assert "components" in result


# More tests would be added for voice verification, transcription, etc.
# These would require test audio files and mocked responses for external services.
