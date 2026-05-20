#!/bin/bash
# Combined startup script for development

echo "🎯 Mencius Agent - Development Environment Setup"
echo "=================================================="

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if conda environment 'men' exists
if ! conda info --envs | grep -q "men"; then
    echo "❌ Conda environment 'men' not found. Please create it first."
    exit 1
fi

echo ""
echo "✅ Found conda environment: men"
echo ""
echo "Starting services in 2 separate terminals..."
echo ""
echo "📌 BACKEND Instructions:"
echo "   Run in Terminal 1: cd $ROOT_DIR && conda activate men && bash backend/run.sh"
echo "   Backend will run on: http://localhost:8000"
echo ""
echo "📌 FRONTEND Instructions:"
echo "   Run in Terminal 2: cd $ROOT_DIR && bash frontend/run.sh"
echo "   Frontend will run on: http://localhost:5173"
echo ""
echo "📌 After both are running:"
echo "   Open browser: http://localhost:5173"
echo ""
