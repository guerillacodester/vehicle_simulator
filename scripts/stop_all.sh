#!/bin/bash
# ArkNet Host Server - Stop All Services
# This script stops the Host Server and all managed subservices

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/.host_server.pid"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}ArkNet Host Server Shutdown${NC}"
echo -e "${CYAN}========================================${NC}"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No PID file found${NC}"
    echo -e "${YELLOW}   Host Server may not be running${NC}"
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Process not found (PID: $PID)${NC}"
    echo -e "${YELLOW}   Removing stale PID file${NC}"
    rm "$PID_FILE"
    exit 0
fi

# Stop Host Server (which will stop all managed services)
echo -e "${YELLOW}⏹️  Stopping Host Server (PID: $PID)...${NC}"

# Try graceful shutdown first
kill -TERM $PID 2>/dev/null || true

# Wait for shutdown
TIMEOUT=15
ELAPSED=0
while ps -p $PID > /dev/null 2>&1 && [ $ELAPSED -lt $TIMEOUT ]; do
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    echo -n "."
done
echo ""

# Force kill if still running
if ps -p $PID > /dev/null 2>&1; then
    echo -e "${RED}⚠️  Graceful shutdown failed, forcing...${NC}"
    kill -KILL $PID 2>/dev/null || true
    sleep 1
fi

# Verify stopped
if ps -p $PID > /dev/null 2>&1; then
    echo -e "${RED}❌ Failed to stop Host Server${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Host Server stopped successfully${NC}"
    rm "$PID_FILE"
fi

echo -e "${CYAN}========================================${NC}"
