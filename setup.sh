#!/bin/bash

# Setup script for Context Management System

echo "========================================="
echo "Context Management System Setup"
echo "SeptemberAI"
echo "========================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env from example if not exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your Groq API key"
fi

# SQLite is built into Python - no database setup needed!
echo "SQLite will be used for storage (no external database required)"

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "To start the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run application: python app.py"
echo "3. Open browser: http://localhost:5000"
echo ""
echo "Note: SQLite database (cms_memory.db) will be created automatically"
echo ""
echo "For development:"
echo "- Run tests: pytest tests/"
echo "- Check examples: python examples/basic_usage.py"
echo ""
