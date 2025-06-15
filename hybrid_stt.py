#!/usr/bin/env python3
"""
CLI tool for testing hybrid STT (Speech-to-Text) system.
This script allows testing the hybrid approach with local and remote processing.
"""
import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from app.audio.processor import process_audio_file
from app.hybrid.controller import process_audio_hybrid


async def process_audio(file_path, verify_speaker=False, use_semantics=False, semantic_threshold=None):
    """Process audio file using hybrid STT system."""
    # Set environment variables for semantic validation if needed
    if use_semantics:
        os.environ["WHISPER_HYBRID_STT_USE_SEMANTIC_VALIDATION"] = "true"
    
    if semantic_threshold is not None:
        os.environ["WHISPER_HYBRID_STT_SEMANTIC_THRESHOLD"] = str(semantic_threshold)
    
    print(f"Processing audio file: {file_path}")
    print(f"Options: verify_speaker={verify_speaker}, use_semantics={use_semantics}")
    
    # Process and normalize the audio file
    processed_audio_path = await process_audio_file(file_path=Path(file_path))
    
    # Process with hybrid approach
    result = await process_audio_hybrid(
        audio_path=processed_audio_path,
        verify_speaker_flag=verify_speaker,
        return_debug=True
    )
    
    # Print results
    print("\n=== Hybrid STT Results ===")
    print(f"Source: {result['source']}")
    print(f"Text: {result['text']}")
    print("\nMetadata:")
    for key, value in result['metadata'].items():
        if value is not None:
            print(f"  {key}: {value}")
    
    # Print formatted JSON
    print("\nJSON Response:")
    print(json.dumps(result, indent=2))
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Test Hybrid STT system')
    parser.add_argument('--file', required=True, help='Path to audio file')
    parser.add_argument('--verify_speaker', action='store_true', help='Verify speaker identity')
    parser.add_argument('--use_semantics', action='store_true', help='Use semantic validation')
    parser.add_argument('--semantic_threshold', type=float, help='Semantic similarity threshold (0.0-1.0)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found")
        sys.exit(1)
    
    # Run async function
    asyncio.run(process_audio(args.file, args.verify_speaker, args.use_semantics, args.semantic_threshold))


if __name__ == "__main__":
    main()
