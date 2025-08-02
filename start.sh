#!/bin/bash

# Production startup script for Hiring Agent on Render

# Exit on any error
set -e

# Set default values if environment variables are not set
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-10000}
export ENVIRONMENT=${ENVIRONMENT:-"production"}

# Create necessary directories
mkdir -p storage/uploads storage/logs

# Set permissions for the startup script
chmod +x start.sh

echo "Starting Hiring Agent in $ENVIRONMENT mode..."
echo "Host: $HOST"
echo "Port: $PORT"

# Start the application with uvicorn for production
exec uvicorn app.main:app \
    --host $HOST \
    --port $PORT \
    --workers 1 \
    --loop uvloop \
    --http httptools \
    --access-log \
    --log-level info