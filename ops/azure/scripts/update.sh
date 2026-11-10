#!/usr/bin/env bash
# New image/artifacts already copied. Back up current env for reversible update.
source "$(dirname "$0")/common.sh"
exec 9>"$AZURE_COMPOSE_DIR/.runtime.lock"
flock -n 9 || { echo 'Another deployment/maintenance operation is running.' >&2; exit 1; }
image=${1:?Usage: update.sh scientific-network-api:tested-tag /absolute/artifact-dir}
artifacts=${2:?Supply versioned artifact directory}
[[ $image =~ ^scientific-network-api:[a-zA-Z0-9._-]+$ && $artifacts = /* && -f $artifacts/manifest.json ]]
"${DOCKER[@]}" image inspect "$image" >/dev/null
cp -p .env ".env.rollback-$(date -u +%Y%m%dT%H%M%SZ)"
python3 - "$image" "$artifacts" <<'PY'
from pathlib import Path
import sys
p=Path('.env')
lines=p.read_text().splitlines()
values={'API_IMAGE':sys.argv[1], 'ARTIFACT_DIR':sys.argv[2]}
p.write_text('\n'.join(k+'='+values[k] if (k:=line.partition('=')[0]) in values else line for line in lines)+'\n')
p.chmod(0o600)
PY
"${COMPOSE[@]}" up -d --no-build --wait --wait-timeout 120 api
"$AZURE_COMPOSE_DIR/scripts/verify.sh"
