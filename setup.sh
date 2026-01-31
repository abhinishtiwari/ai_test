#!/bin/bash

# Soulene Server - Quick Setup Script
# This script helps set up the Soulene server quickly

set -e  # Exit on error

echo "=================================="
echo "🌟 Soulene Server Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.9+ required. You have Python $python_version"
    exit 1
fi

echo "✅ Python $python_version detected"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Setting up environment file..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Please edit .env and add your GOOGLE_API_KEY"
    echo "   Open .env in a text editor and replace 'your_api_key_here' with your actual key"
    echo ""
    read -p "Press Enter when you've added your API key to .env..."
fi

# Validate API key is set
source .env
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_api_key_here" ]; then
    echo "❌ Error: GOOGLE_API_KEY not set in .env file"
    echo "   Please edit .env and add your Google API key"
    exit 1
fi

echo "✅ API key configured"
echo ""

# Final instructions
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To start the server:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run server: python soulene_server.py"
echo "  3. Open chat_interface.html in your browser"
echo ""
echo "Or run: ./run_server.sh"
echo ""
echo "=================================="
