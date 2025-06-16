# Use Python 3.12 as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WHISPER_STORAGE_DIR=/app/storage \
    WHISPER_VOICEPRINT_DIR=/app/storage/voiceprints

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --timeout 2000 -r requirements.txt

# Copy the rest of the application
COPY . .

# Create storage directories
RUN mkdir -p /app/storage/audio /app/storage/voiceprints \
    && chmod -R 755 /app/storage

# Expose the application port
EXPOSE 8000

# Run the application
CMD ["python", "app/main.py"]
