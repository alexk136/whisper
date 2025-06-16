#!/usr/bin/env python3
"""
Test LLM integration for Whisper Voice Auth microservice.
This script helps you test the integration with your Language Model API.
"""
import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv


def test_llm_integration(text, api_url=None, api_key=None):
    """Test LLM API integration with sample text."""
    # Load environment variables
    load_dotenv()
    
    # Use provided values or get from environment
    api_url = api_url or os.environ.get("WHISPER_LLM_API_URL")
    api_key = api_key or os.environ.get("WHISPER_LLM_API_KEY")
    
    if not api_url:
        print("Error: LLM API URL not provided. Use --api-url or set WHISPER_LLM_API_URL")
        return False
    
    # Prepare request
    headers = {
        "Content-Type": "application/json",
    }
    
    # Add API key if provided
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Create payload
    payload = {
        "text": text,
        "metadata": {
            "confidence": 0.95,
            "speaker_match": 0.98,
            "duration": 5.2,
            "language": "ru",
            "source": "whisper_voice_auth_test",
        },
        "source": "whisper_voice_auth",
    }
    
    # Print request details
    print("\n======= REQUEST =======")
    print(f"URL: {api_url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Send request
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30,
        )
        
        # Print response
        print("\n======= RESPONSE =======")
        print(f"Status: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Body: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Body: {response.text}")
        
        # Check success
        if response.status_code == 200:
            print("\n✅ LLM integration test successful!")
            return True
        else:
            print("\n❌ LLM integration test failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test LLM integration for Whisper Voice Auth')
    parser.add_argument('text', help='Text to send to LLM API')
    parser.add_argument('--api-url', help='LLM API URL')
    parser.add_argument('--api-key', help='LLM API Key')
    
    args = parser.parse_args()
    
    success = test_llm_integration(args.text, args.api_url, args.api_key)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
