#!/usr/bin/env bash
# Run on VM after image load, artifact copy, guarded restore and DB verification.
source "$(dirname "$0")/common.sh"
exec 9>"$AZURE_COMPOSE_DIR/.runtime.lock"
flock -n 9 || { echo 'Another deployment/maintenance operation is running.' >&2; exit 1; }
[[ -f .restore-complete ]] || { echo 'Complete the offline restore first.' >&2; exit 1; }
[[ -f .env && $(stat -c%a .env) == 600 ]] || { echo 'Need mode 0600 .env' >&2; exit 1; }
"${COMPOSE[@]}" config --quiet
volume=$("${COMPOSE[@]}" config --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["volumes"]["neo4j-data"]["name"])')
[[ "$(cat .restore-complete)" == "$volume" ]] || { echo 'Restore marker does not match selected production volume.' >&2; exit 1; }
"${COMPOSE[@]}" --profile https up -d --no-build --wait --wait-timeout 240
"$AZURE_COMPOSE_DIR/scripts/verify.sh"
