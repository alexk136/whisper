#!/usr/bin/env python3
"""
Test script for speech recognition using Whisper.
This script transcribes audio files without voice verification.
"""
import os
import argparse
import torch
import whisper
import time


def transcribe_audio(audio_file, model_name="base", language=None):
    """Transcribe audio using Whisper model."""
    start_time = time.time()
    
    # Load the model
    print(f"Loading Whisper model '{model_name}'...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_name, device=device)
    
    # Set options
    options = {
        "language": language,  # None for auto-detection
        "task": "transcribe",
        "fp16": torch.cuda.is_available(),
    }
    
    # Transcribe
    print(f"Transcribing {audio_file} on {device}...")
    result = model.transcribe(audio_file, **options)
    
    # Print results
    text = result["text"].strip()
    language = result.get("language", "unknown")
    
    # Calculate average confidence
    segments = result.get("segments", [])
    if segments:
        confidence = sum(segment.get("confidence", 0) for segment in segments) / len(segments)
    else:
        confidence = 0.0
    
    # Print summary
    elapsed = time.time() - start_time
    print("\nTranscription Results:")
    print("=" * 50)
    print(f"Text: {text}")
    print(f"Language: {language}")
    print(f"Confidence: {confidence:.4f}")
    print(f"Time taken: {elapsed:.2f} seconds")
    print("=" * 50)
    
    return text, language, confidence


def main():
    parser = argparse.ArgumentParser(description='Test Whisper speech recognition')
    parser.add_argument('audio_file', help='Path to audio file')
    parser.add_argument('--model', default='base', choices=['tiny', 'base', 'small', 'medium', 'large'], 
                        help='Whisper model to use')
    parser.add_argument('--language', help='Language code (e.g., "en", "ru") or None for auto-detection')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file '{args.audio_file}' not found")
        return
    
    transcribe_audio(args.audio_file, args.model, args.language)


if __name__ == "__main__":
    main()
