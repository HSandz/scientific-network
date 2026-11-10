#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
# Works before API startup; uses the same limited Python runtime without serving.
"${COMPOSE[@]}" run --rm --no-deps -T api python - < "$AZURE_COMPOSE_DIR/scripts/verify-database.py"
