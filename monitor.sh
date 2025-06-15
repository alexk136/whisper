#!/bin/bash
# Monitoring script for Whisper Voice Auth microservice

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="whisper"
HOST="localhost"
PORT="8000"
HEALTH_ENDPOINT="/health"
NOTIFY_EMAIL=""  # Set your email to receive notifications

# Check if service is running
check_service() {
    response=$(curl -s -o /dev/null -w "%{http_code}" http://$HOST:$PORT$HEALTH_ENDPOINT)
    
    if [ "$response" -eq 200 ]; then
        echo -e "${GREEN}Service is running normally${NC}"
        return 0
    else
        echo -e "${RED}Service is not responding properly (HTTP $response)${NC}"
        return 1
    fi
}

# Get resource usage
check_resources() {
    if command -v docker &> /dev/null; then
        echo -e "\n${YELLOW}Docker Container Stats:${NC}"
        docker stats --no-stream $SERVICE_NAME
        
        echo -e "\n${YELLOW}Container Logs (last 10 lines):${NC}"
        docker logs --tail 10 $SERVICE_NAME
    else
        echo -e "\n${YELLOW}System Resource Usage:${NC}"
        top -b -n 1 | head -n 20
    fi
}

# Monitor continuously
monitor_continuous() {
    clear
    echo -e "${YELLOW}Continuous Monitoring of Whisper Voice Auth${NC}"
    echo "Press Ctrl+C to exit"
    echo "========================================"
    
    while true; do
        echo -e "\n[$(date +"%Y-%m-%d %H:%M:%S")]"
        
        if check_service; then
            # Service is running
            check_resources
        else
            # Service is down
            if [ ! -z "$NOTIFY_EMAIL" ]; then
                echo "Service down! Sending notification to $NOTIFY_EMAIL"
                echo "Whisper Voice Auth service is DOWN at $(date)" | mail -s "ALERT: Whisper Voice Auth Down" $NOTIFY_EMAIL
            fi
        fi
        
        echo -e "\n========================================"
        echo "Refreshing in 60 seconds..."
        sleep 60
        clear
        echo -e "${YELLOW}Continuous Monitoring of Whisper Voice Auth${NC}"
        echo "Press Ctrl+C to exit"
        echo "========================================"
    done
}

# Single check
check_once() {
    echo -e "${YELLOW}Whisper Voice Auth Status Check${NC}"
    echo "========================================"
    
    if check_service; then
        check_resources
    fi
    
    echo -e "\n========================================"
}

# Parse arguments
case "$1" in
    --continuous|-c)
        monitor_continuous
        ;;
    *)
        check_once
        ;;
esac
