#!/usr/bin/env python3
"""
Generate a secure encryption key for Whisper Voice Auth microservice.
"""
import base64
import os
from cryptography.fernet import Fernet

# Generate a Fernet key
key = Fernet.generate_key()
key_str = key.decode('utf-8')

print("\nGenerated encryption key:")
print(key_str)
print("\nAdd this to your .env file as:")
print(f"WHISPER_ENCRYPTION_KEY={key_str}\n")

# Update .env file if it exists
env_file = '.env'
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Replace existing key or add new one
    if 'WHISPER_ENCRYPTION_KEY=' in env_content:
        lines = env_content.split('\n')
        updated_lines = []
        for line in lines:
            if line.startswith('WHISPER_ENCRYPTION_KEY='):
                updated_lines.append(f'WHISPER_ENCRYPTION_KEY={key_str}')
            else:
                updated_lines.append(line)
        updated_content = '\n'.join(updated_lines)
    else:
        updated_content = env_content + f'\nWHISPER_ENCRYPTION_KEY={key_str}\n'
    
    with open(env_file, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated {env_file} with the new encryption key.")
