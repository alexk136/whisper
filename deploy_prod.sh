#!/bin/bash
# Deploy Whisper Voice Auth microservice in production mode

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Deploying Whisper Voice Auth in production mode${NC}"
echo "=================================================="

# Check for production environment file
if [ ! -f ".env.prod" ]; then
    echo -e "${RED}Error: .env.prod file not found${NC}"
    echo "Please create it from the sample:"
    echo "cp .env.prod.sample .env.prod"
    echo "Then edit it with your production settings."
    exit 1
fi

# Check for encryption key
if ! grep -q "WHISPER_ENCRYPTION_KEY" .env.prod; then
    echo -e "${RED}Error: WHISPER_ENCRYPTION_KEY not found in .env.prod${NC}"
    echo "Please run: python generate_key.py"
    echo "And add the key to .env.prod"
    exit 1
fi

# Check for API key
if grep -q "complex-production-api-key-here" .env.prod; then
    echo -e "${RED}Error: Default API key detected in .env.prod${NC}"
    echo "Please change the API key to a secure value"
    exit 1
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker not found${NC}"
    echo "Please install Docker"
    exit 1
fi

# Pull latest changes if in a git repository
if [ -d ".git" ]; then
    echo "Pulling latest changes..."
    git pull
fi

# Build and start the service
echo "Building and starting the service..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Check if service is running
echo "Checking if service is running..."
sleep 5
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}Service is running!${NC}"
    echo "API available at: http://localhost:8000/api/v1"
else
    echo -e "${RED}Service not responding. Check logs with:${NC}"
    echo "docker compose -f docker-compose.prod.yml logs"
fi

echo "=================================================="
echo -e "${GREEN}Deployment complete!${NC}"
echo 
echo "To view logs:"
echo "docker compose -f docker-compose.prod.yml logs -f"
echo
echo "To stop the service:"
echo "docker compose -f docker-compose.prod.yml down"
echo "=================================================="
