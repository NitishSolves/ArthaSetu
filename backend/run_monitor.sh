#!/bin/bash

# ============================================
# Run Agent Monitoring Script
# ============================================

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

# Run monitor with all arguments passed through
python agents/monitor.py "$@"
