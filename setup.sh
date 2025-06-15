#!/bin/bash
# Setup script for Whisper Voice Auth microservice

set -e  # Exit on error

# Check Python version
python_version=$(python3 --version | cut -d" " -f2)
if [[ $(echo "$python_version" | cut -d. -f1,2 | sed 's/\.//') -lt 312 ]]; then
    echo "Warning: Python 3.12+ is recommended. You have $python_version"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "Creating storage directories..."
mkdir -p storage/audio storage/voiceprints

# Generate encryption key if not exists
if ! grep -q "WHISPER_ENCRYPTION_KEY" .env 2>/dev/null; then
    echo "Generating encryption key..."
    python generate_key.py
fi

# Check for FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: FFmpeg not found. This is required for audio processing."
    echo "Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: choco install ffmpeg"
fi

# Success message
echo "=================================================="
echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Record voice samples: ./record_samples.py"
echo "2. Register your voice: ./test_client.py register samples/*.wav"
echo "3. Test verification: ./test_client.py verify test_audio.wav"
echo "4. Start the service: python app/main.py"
echo ""
echo "For Docker setup:"
echo "docker-compose up -d"
echo "=================================================="
