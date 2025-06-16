#!/usr/bin/env python3
"""
Test script for the Whisper Voice Auth microservice.
This script allows registering a voice print and testing voice verification.
"""
import argparse
import os
import requests
import json
from pathlib import Path


def register_voice(api_url, api_key, audio_files):
    """Register voice print with audio files."""
    files = [('audio_files', (os.path.basename(f), open(f, 'rb'), 'audio/wav')) for f in audio_files]
    
    headers = {
        'X-API-Key': api_key,
    }
    
    response = requests.post(
        f"{api_url}/api/v1/voice/register",
        headers=headers,
        files=files
    )
    
    print(f"Status code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    return response.json()


def verify_voice(api_url, api_key, audio_file):
    """Verify voice with an audio file."""
    files = {
        'audio_file': (os.path.basename(audio_file), open(audio_file, 'rb'), 'audio/wav')
    }
    
    headers = {
        'X-API-Key': api_key,
    }
    
    response = requests.post(
        f"{api_url}/api/v1/voice/verify",
        headers=headers,
        files=files
    )
    
    print(f"Status code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    return response.json()


def main():
    parser = argparse.ArgumentParser(description='Test Whisper Voice Auth microservice')
    parser.add_argument('--url', default='http://localhost:8000', help='API URL')
    parser.add_argument('--key', default='your-secret-api-key-here', help='API Key')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register voice print')
    register_parser.add_argument('audio_files', nargs='+', help='Audio files containing the owner\'s voice')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify voice')
    verify_parser.add_argument('audio_file', help='Audio file to verify')
    
    args = parser.parse_args()
    
    if args.command == 'register':
        register_voice(args.url, args.key, args.audio_files)
    elif args.command == 'verify':
        verify_voice(args.url, args.key, args.audio_file)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
