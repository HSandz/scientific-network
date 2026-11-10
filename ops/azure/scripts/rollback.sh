#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
exec 9>"$AZURE_COMPOSE_DIR/.runtime.lock"
flock -n 9 || { echo 'Another deployment/maintenance operation is running.' >&2; exit 1; }
prior=${1:?Usage: rollback.sh .env.rollback-UTCSTAMP}
[[ "$prior" == .env.rollback-* && -f "$prior" && ! -L "$prior" ]]
cp -p "$prior" .env
"${COMPOSE[@]}" up -d --no-deps --no-build --pull never --wait --wait-timeout 120 api
"$AZURE_COMPOSE_DIR/scripts/verify.sh"
