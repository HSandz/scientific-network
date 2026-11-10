#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
"${COMPOSE[@]}" --profile https logs --tail="${LINES:-100}" "$@"
