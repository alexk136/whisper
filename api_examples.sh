#!/bin/bash
# API examples for Whisper Voice Auth microservice

# Set API URL and key
API_URL="http://localhost:8000"
API_KEY="your-secret-api-key-here"  # Change this to your actual API key

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Whisper Voice Auth API Examples${NC}"
echo "=================================="

# Health check
echo -e "${GREEN}1. Health Check${NC}"
echo "curl -X GET $API_URL/health"
echo

# Register voice - upload multiple audio files
echo -e "${GREEN}2. Register Voice Print${NC}"
echo "curl -X POST \\
  $API_URL/api/v1/voice/register \\
  -H \"X-API-Key: $API_KEY\" \\
  -F \"audio_files=@./samples/sample_1.wav\" \\
  -F \"audio_files=@./samples/sample_2.wav\" \\
  -F \"audio_files=@./samples/sample_3.wav\""
echo

# Verify voice - upload audio file
echo -e "${GREEN}3. Verify Voice - File Upload${NC}"
echo "curl -X POST \\
  $API_URL/api/v1/voice/verify \\
  -H \"X-API-Key: $API_KEY\" \\
  -F \"audio_file=@./test_command.wav\""
echo

# Verify voice - from URL
echo -e "${GREEN}4. Verify Voice - From URL${NC}"
echo "curl -X POST \\
  $API_URL/api/v1/voice/verify \\
  -H \"X-API-Key: $API_KEY\" \\
  -H \"Content-Type: application/json\" \\
  -d '{\"audio_url\": \"https://example.com/audio.wav\"}'"
echo

echo -e "${YELLOW}Notes:${NC}"
echo "- Replace 'your-secret-api-key-here' with your actual API key"
echo "- Make sure the server is running before testing these commands"
echo "- For voice registration, use 3 samples of your voice (10+ seconds each)"
echo "- For verification, record a command you want to process"
echo "=================================="
