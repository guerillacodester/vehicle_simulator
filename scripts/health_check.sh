#!/bin/bash
# ArkNet Host Server - Health Check
# This script checks if the Host Server and managed services are healthy

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/.host_server.pid"
HOST_URL="http://localhost:6000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}ArkNet Services Health Check${NC}"
echo -e "${CYAN}========================================${NC}"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${RED}❌ Host Server not running (no PID file)${NC}"
    exit 1
fi

PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${RED}❌ Host Server process not found (PID: $PID)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Host Server process running (PID: $PID)${NC}"

# Check HTTP health endpoint
if ! command -v curl &> /dev/null; then
    echo -e "${YELLOW}⚠️  curl not installed, skipping HTTP check${NC}"
    exit 0
fi

echo -e "${CYAN}🔍 Checking HTTP health endpoint...${NC}"

RESPONSE=$(curl -s -w "\n%{http_code}" "$HOST_URL/health" 2>/dev/null || echo -e "\n000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Host Server API healthy (HTTP $HTTP_CODE)${NC}"
    
    # Parse and display services status if jq is available
    if command -v jq &> /dev/null; then
        echo ""
        echo -e "${CYAN}📊 Services Status:${NC}"
        echo "$BODY" | jq -r '.services | to_entries[] | "  \(.key): \(.value.status)"' 2>/dev/null || echo "$BODY"
    else
        echo "$BODY" | head -c 500
    fi
else
    echo -e "${RED}❌ Host Server API unhealthy (HTTP $HTTP_CODE)${NC}"
    exit 1
fi

echo -e "${CYAN}========================================${NC}"
exit 0
