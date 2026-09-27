#!/bin/bash

# ============================================
# Run Background Scheduler Service
# ============================================

echo "Starting Financial Coaching Agent Background Service"
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY environment variable not set"
    echo ""
    echo "Please set your API key:"
    echo "  export OPENROUTER_API_KEY=\"your-key-here\""
    echo ""
    exit 1
fi

# Check command line arguments
if [ "$1" == "--once" ]; then
    echo "Running one-time analysis for all users..."
    python agents/scheduler.py
elif [ "$1" == "--user" ]; then
    if [ -z "$2" ]; then
        echo "ERROR: User ID required"
        echo "Usage: ./run_service.sh --user <user_id>"
        exit 1
    fi
    echo "Running analysis for user: $2"
    python agents/scheduler.py --user "$2"
elif [ "$1" == "--scheduled" ]; then
    INTERVAL=${2:-3600}
    echo "Starting scheduled service (interval: ${INTERVAL}s)"
    echo "Press Ctrl+C to stop"
    echo ""
    python agents/scheduler.py --scheduled "$INTERVAL"
else
    echo "Usage:"
    echo "  ./run_service.sh --once                    # Run once for all users"
    echo "  ./run_service.sh --user <user_id>          # Run for specific user"
    echo "  ./run_service.sh --scheduled [interval]    # Run as background service"
    echo ""
    echo "Examples:"
    echo "  ./run_service.sh --once"
    echo "  ./run_service.sh --user 153735c8-b1e3-4fc6-aa4e-7deb6454990b"
    echo "  ./run_service.sh --scheduled 3600          # Run every hour"
    echo "  ./run_service.sh --scheduled 1800          # Run every 30 minutes"
fi
