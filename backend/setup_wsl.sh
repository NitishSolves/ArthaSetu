#!/bin/bash

# ============================================
# Spare Backend Setup Script for WSL
# ============================================

set -e  # Exit on error

echo "================================================"
echo "  Financial Coaching Agent - WSL Setup"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Update system
echo -e "${YELLOW}[1/6]${NC} Updating system packages..."
sudo apt-get update -qq

# Step 2: Install Node.js (for MCP server)
echo -e "${YELLOW}[2/6]${NC} Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
echo -e "${GREEN}OK${NC} Node.js $(node --version) installed"

# Step 3: Install Python 3.11+
echo -e "${YELLOW}[3/6]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    sudo apt-get install -y python3 python3-pip python3-venv
fi
echo -e "${GREEN}OK${NC} Python $(python3 --version) installed"

# Step 4: Create Python virtual environment
echo -e "${YELLOW}[4/6]${NC} Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}OK${NC} Virtual environment created and activated"

# Step 5: Install Python dependencies
echo -e "${YELLOW}[5/6]${NC} Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}OK${NC} Python dependencies installed"

# Step 6: Install PostgreSQL MCP server
echo -e "${YELLOW}[6/6]${NC} Installing PostgreSQL MCP server..."
npm install -g @modelcontextprotocol/server-postgres
echo -e "${GREEN}OK${NC} PostgreSQL MCP server installed"

echo ""
echo "================================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================================"
echo ""
echo "To run the agent:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Run agent: python agents/financial_agent.py --interactive"
echo ""
echo "Or run directly:"
echo "  ./run.sh"
echo ""
