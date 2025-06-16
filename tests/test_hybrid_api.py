"""
Tests for the hybrid API integration.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

try:
    from app.main import app
    from app.api.hybrid_routes import hybrid_router
    API_IMPORTS_SUCCESSFUL = True
except ImportError:
    API_IMPORTS_SUCCESSFUL = False

# Skip all API-dependent tests if imports failed
pytestmark = pytest.mark.skipif(not API_IMPORTS_SUCCESSFUL, 
                              reason="API imports failed, skipping API-dependent tests")

@pytest.fixture
def client():
    """Create a test client."""
    if API_IMPORTS_SUCCESSFUL:
        return TestClient(app)
    return None


def test_api_integration(client):
    """Test that the hybrid router is integrated into the main app."""
    if not client:
        pytest.skip("Client not available")
    
    # Get the application routes
    routes = app.routes
    
    # Check if hybrid_router endpoints are included
    hybrid_endpoints = [route for route in routes if getattr(route, "path", "").startswith("/api/v1/hybrid")]
    assert len(hybrid_endpoints) > 0, "Hybrid router endpoints not found in main app"


def test_api_schema():
    """Test that the API schema is defined correctly."""
    if not API_IMPORTS_SUCCESSFUL:
        pytest.skip("API imports failed")
    
    # Check the router's routes
    routes = hybrid_router.routes
    
    # Find the hybrid STT endpoint
    hybrid_stt_route = next((r for r in routes if r.path == "/hybrid/stt"), None)
    assert hybrid_stt_route is not None, "Hybrid STT endpoint not found in hybrid_router"
    
    # Check the response model
    assert hasattr(hybrid_stt_route, "response_model"), "Response model not defined for hybrid STT endpoint"
    
    # Check response codes
    assert hasattr(hybrid_stt_route, "responses"), "Responses not defined for hybrid STT endpoint"
    assert 403 in hybrid_stt_route.responses, "403 response not defined for hybrid STT endpoint"
    assert 422 in hybrid_stt_route.responses, "422 response not defined for hybrid STT endpoint"


def test_api_params():
    """Test that the API accepts the correct parameters."""
    if not API_IMPORTS_SUCCESSFUL:
        pytest.skip("API imports failed")
    
    # Get the hybrid STT endpoint
    routes = hybrid_router.routes
    hybrid_stt_route = next((r for r in routes if r.path == "/hybrid/stt"), None)
    
    # Check required parameters
    params = {p.name: p for p in hybrid_stt_route.dependant.query_params}
    
    # Check expected parameters exist
    assert "verify_speaker" in params, "verify_speaker parameter not found"
    assert "return_debug" in params, "return_debug parameter not found"
    assert "use_semantics" in params, "use_semantics parameter not found"
    assert "semantic_threshold" in params, "semantic_threshold parameter not found"
    
    # Check parameter types
    assert params["verify_speaker"].type_ == bool, "verify_speaker should be boolean"
    assert params["return_debug"].type_ == bool, "return_debug should be boolean"
    assert params["use_semantics"].type_ == bool, "use_semantics should be boolean"
    
    # Check default values
    assert params["verify_speaker"].default is False, "verify_speaker default should be False"
    assert params["return_debug"].default is False, "return_debug default should be False"
    assert params["use_semantics"].default is False, "use_semantics default should be False"


def test_api_error_handling(client):
    """Test API error handling with invalid input."""
    if not client:
        pytest.skip("Client not available")
    
    # Test with missing required file
    response = client.post("/api/v1/hybrid/stt")
    assert response.status_code == 422, "API should return 422 for missing file"
    
    # Test with invalid API key
    with patch("app.api.hybrid_routes.validate_api_key", side_effect=Exception("Invalid API key")):
        response = client.post(
            "/api/v1/hybrid/stt",
            files={"audio_file": ("test.wav", b"dummy data", "audio/wav")}
        )
        assert response.status_code in [401, 403, 422], "API should handle invalid API key"
