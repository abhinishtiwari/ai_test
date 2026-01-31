#!/bin/bash

# Soulene Server - Run Script
# Quick script to start the server

set -e

echo "🌟 Starting Soulene Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run setup.sh first"
    exit 1
fi

# Run the server
python soulene_server.py
