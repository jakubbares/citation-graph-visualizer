#!/bin/bash

# Script to start the backend server

echo "🚀 Starting Citation Graph Visualizer Backend..."
echo ""

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit backend/.env and add your API keys!"
    echo ""
fi

# Start the server
echo "Starting FastAPI server on http://localhost:8000..."
echo "API docs available at: http://localhost:8000/docs"
echo ""
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
