#!/bin/bash

# Start script for production deployment
set -e

echo "Starting Telegram Image AI Bot..."

# Set default port if not provided
export PORT=${PORT:-5000}

# Enable webhook mode for production
export USE_WEBHOOK=true

# Validate required environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN is required"
    exit 1
fi

echo "Configuration validated successfully"
echo "Starting bot on port $PORT with webhook mode enabled"

# Start the application
exec python working_bot.py