#!/bin/bash
# ArkNet Host Server - Start All Services
# This script starts the Host Server which manages all subservices

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv"
PYTHON="$VENV_PATH/bin/python"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/.host_server.pid"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}ArkNet Host Server Startup${NC}"
echo -e "${CYAN}========================================${NC}"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Host Server already running (PID: $PID)${NC}"
        echo -e "${YELLOW}   Use stop_all.sh to stop it first${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠️  Stale PID file found, removing...${NC}"
        rm "$PID_FILE"
    fi
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Check Python venv
if [ ! -f "$PYTHON" ]; then
    echo -e "${RED}❌ Python virtualenv not found at: $VENV_PATH${NC}"
    echo -e "${YELLOW}   Run: python -m venv venv${NC}"
    exit 1
fi

# Check dependencies
echo -e "${CYAN}🔍 Checking dependencies...${NC}"
if ! "$PYTHON" -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Missing dependencies, installing...${NC}"
    "$VENV_PATH/bin/pip" install -q fastapi uvicorn httpx
fi

echo -e "${GREEN}✅ Dependencies OK${NC}"

# Start Host Server in background
echo -e "${CYAN}🚀 Starting Host Server...${NC}"
cd "$PROJECT_ROOT"

nohup "$PYTHON" -m services.host_server --host 0.0.0.0 --port 6000 \
    > "$LOG_DIR/host_server.log" 2>&1 &

SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

# Wait for startup
echo -e "${YELLOW}⏳ Waiting for Host Server to start...${NC}"
sleep 2

# Check if process is running
if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Host Server started successfully!${NC}"
    echo -e "${GREEN}   PID:     $SERVER_PID${NC}"
    echo -e "${GREEN}   URL:     http://localhost:6000${NC}"
    echo -e "${GREEN}   Health:  http://localhost:6000/health${NC}"
    echo -e "${GREEN}   Logs:    tail -f $LOG_DIR/host_server.log${NC}"
    echo ""
    echo -e "${CYAN}📋 Next Steps:${NC}"
    echo -e "${CYAN}   1. Start simulator:  curl -X POST http://localhost:6000/api/services/simulator/start${NC}"
    echo -e "${CYAN}   2. Connect console:  python -m clients.fleet${NC}"
    echo -e "${CYAN}   3. Check services:   services${NC}"
else
    echo -e "${RED}❌ Failed to start Host Server${NC}"
    echo -e "${RED}   Check logs: $LOG_DIR/host_server.log${NC}"
    rm "$PID_FILE"
    exit 1
fi

echo -e "${CYAN}========================================${NC}"
