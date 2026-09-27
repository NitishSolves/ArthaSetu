#!/bin/bash

# ============================================
# Start Spare Backend Server (FastAPI)
# ============================================

echo "╔════════════════════════════════════════════════════════╗"
echo "║    Agente AI - Spare Backend Starting                 ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Navigate to backend_spare directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "✗ Virtual environment not found!"
    echo "  Please run ./setup_wsl.sh first"
    exit 1
fi

# Check if required packages are installed
echo "✓ Checking dependencies..."
python -c "import fastapi, uvicorn, autogen_agentchat, autogen_ext" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✗ Missing dependencies!"
    echo "  Installing requirements..."
    pip install -r requirements.txt
fi

# Check if MCP config exists
if [ ! -f ".mcp.json" ] && [ ! -f "mcp.json" ]; then
    echo "✗ MCP config not found!"
    echo "  Expected: .mcp.json or mcp.json"
    exit 1
fi

echo "✓ All checks passed"
echo ""

# Display connection info
echo "╔════════════════════════════════════════════════════════╗"
echo "║              Backend Connection Info                   ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "  Frontend (Windows) can connect to:"
echo "    → http://localhost:8000"
echo "    → http://127.0.0.1:8000"
echo ""
echo "  API Endpoints:"
echo "    POST /api/analyze          - Trigger analysis (async)"
echo "    POST /api/analyze-sync     - Trigger analysis (sync)"
echo "    GET  /api/status/{user_id} - Get analysis status"
echo "    GET  /api/health           - Health check"
echo ""
echo "  API Documentation:"
echo "    → http://localhost:8000/docs"
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║         Press Ctrl+C to stop the server                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Start FastAPI server
python main.py
