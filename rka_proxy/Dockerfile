# RKA Proxy — Remote Keybox Attestation Service
# Docker container for forwarding Play Integrity challenges to physical devices

FROM python:3.11-slim

LABEL maintainer="Titan Team"
LABEL description="Remote Keybox Attestation Proxy for Play Integrity"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    android-tools-adb \
    usbutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .
COPY device_pool.py .

# Create non-root user (but ADB needs root for USB)
# Running as root for USB device access

# Expose API port
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ADB_VENDOR_KEYS=/root/.android

# Start ADB server and run the API
CMD ["sh", "-c", "adb start-server && uvicorn server:app --host 0.0.0.0 --port 8090"]
