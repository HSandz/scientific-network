#!/usr/bin/env bash
# API-only transaction. Previous image/artifacts remain available for rollback.
source "$(dirname "$0")/common.sh"
exec 9>"$AZURE_COMPOSE_DIR/.runtime.lock"
flock -n 9 || { echo 'Another deployment/maintenance operation is running.' >&2; exit 1; }
image=${1:?Usage: update.sh scientific-network-api:tested-tag /absolute/artifact-dir}
artifacts=${2:?Supply versioned artifact directory}
[[ $image =~ ^scientific-network-api:[a-zA-Z0-9._-]+$ && $artifacts = /* && -f $artifacts/manifest.json ]]
[[ -f .env && ! -L .env && $(stat -c%a .env) == 600 ]]
"${DOCKER[@]}" image inspect "$image" >/dev/null
"${COMPOSE[@]}" config --quiet
snapshot=$(mktemp "$AZURE_COMPOSE_DIR/.env.rollback-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
cp -p .env "$snapshot"
changed=false
recover() {
  rc=$?
  trap - EXIT HUP INT TERM
  if [[ $changed == true && $rc != 0 ]]; then
    echo 'Deployment failed; restoring exact previous configuration.' >&2
    cp -p "$snapshot" .env
    # Already hold lock 9: never call rollback.sh, which acquires it again.
    if "${COMPOSE[@]}" up -d --no-deps --no-build --pull never --wait --wait-timeout 120 api &&
       "$AZURE_COMPOSE_DIR/scripts/verify.sh"; then
      echo 'Previous API restored and verified.' >&2
    else
      echo 'CRITICAL: rollback verification failed; operator intervention required.' >&2
      exit 70
    fi
  fi
  exit "$rc"
}
trap recover EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
changed=true
python3 - "$image" "$artifacts" <<'PY'
from pathlib import Path
import os
import sys
p=Path('.env')
lines=p.read_text().splitlines()
values={'API_IMAGE':sys.argv[1], 'ARTIFACT_DIR':sys.argv[2]}
assert all(sum(line.startswith(k+'=') for line in lines)==1 for k in values)
tmp=p.with_name('.env.update')
fd=os.open(tmp, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as f:
    f.write('\n'.join(k+'='+values[k] if (k:=line.partition('=')[0]) in values else line for line in lines)+'\n')
os.replace(tmp,p)
PY
"${COMPOSE[@]}" up -d --no-deps --no-build --pull never --wait --wait-timeout 120 api
"$AZURE_COMPOSE_DIR/scripts/verify.sh"
echo "Deployment verified; rollback snapshot: $(basename "$snapshot")"
