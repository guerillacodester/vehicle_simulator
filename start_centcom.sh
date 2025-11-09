#!/bin/bash
# Cross-platform launcher for gpscentcom_server
# Usage: ./start_centcom.sh [console|service] [config_path]

MODE=${1:-console}
CONFIG=${2:-config.ini}
PYTHON_BIN=${PYTHON_BIN:-python3}

cd "$(dirname "$0")"

if [ "$MODE" = "console" ]; then
    echo "Launching CentCom in CONSOLE mode with $CONFIG"
    exec $PYTHON_BIN -m gpscentcom_server --config "$CONFIG"
else
    echo "Launching CentCom as SERVICE with $CONFIG"
    nohup $PYTHON_BIN -m gpscentcom_server --config "$CONFIG" > centcom.log 2>&1 &
    echo "CentCom started as background service. Logs: centcom.log"
fi
