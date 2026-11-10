#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
exec 9>"$AZURE_COMPOSE_DIR/.runtime.lock"
flock -n 9 || { echo 'Another deployment/maintenance operation is running.' >&2; exit 1; }
prior=${1:?Usage: rollback.sh .env.rollback-UTCSTAMP}
[[ "$prior" == .env.rollback-* && -f "$prior" && ! -L "$prior" ]]
cp -p "$prior" .env
"${COMPOSE[@]}" --profile https up -d --no-build --wait --wait-timeout 240
"$AZURE_COMPOSE_DIR/scripts/verify.sh"
