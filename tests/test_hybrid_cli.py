"""
Tests for the hybrid_stt.py CLI tool.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Adjust path to import the CLI script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import hybrid_stt
    HYBRID_CLI_IMPORTS_SUCCESSFUL = True
except ImportError:
    HYBRID_CLI_IMPORTS_SUCCESSFUL = False

# Skip all CLI-dependent tests if imports failed
pytestmark = pytest.mark.skipif(not HYBRID_CLI_IMPORTS_SUCCESSFUL, 
                               reason="CLI imports failed, skipping CLI-dependent tests")

@pytest.fixture
def sample_audio_path():
    """Create a simple mock audio file for testing."""
    # Create a temporary test file
    import tempfile
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp.write(b"mock audio data")
    temp.close()
    return temp.name


@pytest.mark.asyncio
async def test_process_audio_cli(sample_audio_path):
    """Test the CLI process_audio function."""
    if not HYBRID_CLI_IMPORTS_SUCCESSFUL:
        pytest.skip("CLI imports failed")
    
    # Mock the required dependencies
    with patch("hybrid_stt.process_audio_file") as mock_process:
        with patch("hybrid_stt.process_audio_hybrid") as mock_hybrid:
            # Setup the mocks
            mock_process.return_value = Path("/tmp/processed_audio.wav")
            mock_hybrid.return_value = {
                "source": "local",
                "text": "тестовый текст",
                "metadata": {
                    "confidence": 0.95,
                    "speaker_match": None,
                    "duration": 3.5,
                    "language": "ru",
                    "fallback_used": False,
                    "semantic_diff": None
                }
            }
            
            # Call the function
            result = await hybrid_stt.process_audio(
                file_path=sample_audio_path,
                verify_speaker=False,
                use_semantics=False
            )
            
            # Check results
            assert result["source"] == "local"
            assert result["text"] == "тестовый текст"
            assert result["metadata"]["confidence"] == 0.95
            assert result["metadata"]["fallback_used"] == False
            
            # Verify mocks were called
            mock_process.assert_called_once()
            mock_hybrid.assert_called_once()


def test_cli_argument_parsing():
    """Test CLI argument parsing."""
    if not HYBRID_CLI_IMPORTS_SUCCESSFUL:
        pytest.skip("CLI imports failed")
    
    # Test argument parsing
    test_args = ["hybrid_stt.py", "--file", "/path/to/audio.wav", "--verify_speaker", "--use_semantics", "--semantic_threshold", "0.8"]
    
    with patch("sys.argv", test_args):
        with patch("hybrid_stt.asyncio.run") as mock_run:
            # Call the main function which parses arguments
            hybrid_stt.main()
            
            # Verify the arguments were parsed correctly and passed to process_audio
            call_args, call_kwargs = mock_run.call_args
            assert call_args[0] == "/path/to/audio.wav"
            assert call_kwargs["verify_speaker"] == True
            assert call_kwargs["use_semantics"] == True
            assert call_kwargs["semantic_threshold"] == 0.8


def test_cli_environment_variables():
    """Test that CLI sets environment variables correctly."""
    if not HYBRID_CLI_IMPORTS_SUCCESSFUL:
        pytest.skip("CLI imports failed")
    
    # Mock environment
    with patch.dict(os.environ, {}, clear=True):
        # Mock asyncio.run to avoid actual execution
        with patch("hybrid_stt.asyncio.run"):
            # Call process_audio with use_semantics=True
            hybrid_stt.process_audio("/path/to/audio.wav", use_semantics=True, semantic_threshold=0.75)
            
            # Check that environment variables were set
            assert os.environ.get("WHISPER_HYBRID_STT_USE_SEMANTIC_VALIDATION") == "true"
            assert os.environ.get("WHISPER_HYBRID_STT_SEMANTIC_THRESHOLD") == "0.75"
