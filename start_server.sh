#!/bin/bash

# Start Context Management System Server
echo "Starting Context Management System..."

# Set your GROQ API key here or export it in your environment
export GROQ_API_KEY="${GROQ_API_KEY:-your_groq_api_key_here}"
export SQLITE_DB_PATH="cms_memory.db"
export FLASK_ENV="development"
export FLASK_DEBUG="True"

python3 app.py --port 5001
