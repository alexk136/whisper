#!/usr/bin/env python3
"""
Record audio samples for voice print registration.
This script helps you record audio samples that can be used to register your voice print.
"""
import os
import time
import argparse
import wave
import numpy as np
import pyaudio

# Audio recording parameters
RATE = 16000
CHANNELS = 1
CHUNK = 1024
FORMAT = pyaudio.paInt16
OUTPUT_DIR = "samples"

def record_audio(output_file, duration=10, rate=RATE, channels=CHANNELS, chunk=CHUNK):
    """Record audio from microphone."""
    p = pyaudio.PyAudio()
    
    # Open stream
    stream = p.open(
        format=FORMAT,
        channels=channels,
        rate=rate,
        input=True,
        frames_per_buffer=chunk
    )
    
    print(f"Recording for {duration} seconds...")
    frames = []
    
    # Countdown
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("GO! Recording...")
    
    # Record audio
    for _ in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)
    
    print("Done recording.")
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save the recorded audio
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    wf = wave.open(output_file, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"Audio saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Record audio samples for voice print registration.')
    parser.add_argument('--samples', type=int, default=3, help='Number of samples to record')
    parser.add_argument('--duration', type=int, default=10, help='Duration of each sample in seconds')
    parser.add_argument('--output-dir', default=OUTPUT_DIR, help='Directory to save samples')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Will record {args.samples} samples, each {args.duration} seconds long.")
    print("Speak naturally during the recording. Read a text or count numbers.")
    print("Make sure you are in a quiet environment.")
    input("Press Enter to start recording...")
    
    # Record samples
    for i in range(1, args.samples + 1):
        output_file = os.path.join(args.output_dir, f"sample_{i}.wav")
        
        print(f"\nRecording sample {i}/{args.samples}")
        record_audio(output_file, duration=args.duration)
        
        if i < args.samples:
            input("Press Enter to record the next sample...")
    
    print("\nAll samples recorded. You can now register your voice print using:")
    print(f"./test_client.py register {' '.join([os.path.join(args.output_dir, f'sample_{i}.wav') for i in range(1, args.samples + 1)])}")


if __name__ == "__main__":
    main()
