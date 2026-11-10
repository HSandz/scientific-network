#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
"${DOCKER[@]}" stats --no-stream
free -h
swapon --show
df -h /
vmstat 1 3
python3 "$AZURE_COMPOSE_DIR/scripts/resource-snapshot.py"
