#!/bin/bash

# Demo script for Citation Graph Visualizer
# This script demonstrates the API functionality

API_URL="http://localhost:8000"

echo "🧪 Citation Graph Visualizer - API Demo"
echo "========================================"
echo ""

# Check if backend is running
echo "1. Checking if backend is running..."
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ "$response" != "200" ]; then
    echo "❌ Backend is not running!"
    echo "   Please start the backend first:"
    echo "   ./start-backend.sh"
    exit 1
fi

echo "✅ Backend is running!"
echo ""

# Test root endpoint
echo "2. Testing root endpoint..."
curl -s $API_URL | python3 -m json.tool
echo ""

# List graphs
echo "3. Listing all graphs..."
curl -s $API_URL/api/graphs | python3 -m json.tool
echo ""

echo "========================================"
echo "✅ API Demo Complete!"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Upload some PDF papers"
echo "3. Build a citation graph"
echo "4. Extract features and visualize"
echo ""
echo "For full API documentation:"
echo "http://localhost:8000/docs"
