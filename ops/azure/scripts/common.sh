#!/usr/bin/env bash
set -euo pipefail
AZURE_COMPOSE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$AZURE_COMPOSE_DIR"
# SSH user need not join Docker's root-equivalent group.
if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
else
  DOCKER=(sudo -n docker)
fi
COMPOSE=("${DOCKER[@]}" compose --env-file "$AZURE_COMPOSE_DIR/.env" -f "$AZURE_COMPOSE_DIR/compose.yaml")
