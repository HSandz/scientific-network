#!/usr/bin/env bash
# Operator-only fault injection on a separate Compose project, no volumes/data.
source "$(dirname "$0")/common.sh"
image=$("${COMPOSE[@]}" config --format json | python3 -c 'import json,sys;print(json.load(sys.stdin)["services"]["api"]["image"])')
testdir=$(mktemp -d /tmp/azure-rollback-test-XXXXXX)
name="scientific-network-rollback-test-$$"
old="scientific-network-api:rollback-good-$$"
bad="scientific-network-api:rollback-fault-$$"
cleanup() {
  docker compose --env-file "$testdir/.env" -f "$testdir/compose.yaml" rm -sf api >/dev/null 2>&1 || true
  docker image rm "$old" "$bad" >/dev/null 2>&1 || true
  rm -rf "$testdir"
}
[[ $(id -u) == 0 ]] || { echo 'Run test as root (no Docker group needed).' >&2; exit 1; }
trap cleanup EXIT
mkdir "$testdir/scripts" "$testdir/artifacts"
cp "$AZURE_COMPOSE_DIR/scripts/"{common.sh,update.sh,rollback.sh} "$testdir/scripts/"
echo '{}' > "$testdir/artifacts/manifest.json"
printf 'API_IMAGE=%s\nARTIFACT_DIR=%s/artifacts\n' "$old" "$testdir" > "$testdir/.env"
chmod 600 "$testdir/.env"
cp "$testdir/.env" "$testdir/original"
docker image tag "$image" "$old"
docker image tag "$image" "$bad"
cat > "$testdir/compose.yaml" <<YAML
name: $name
services:
  api:
    image: \${API_IMAGE}
    network_mode: none
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 64m
    pids_limit: 32
    entrypoint: [python, -m, http.server, '8000']
    environment:
      TEST_IMAGE: \${API_IMAGE}
    healthcheck:
      test: [CMD, python, -c, 'import os,urllib.request; assert "rollback-fault" not in os.environ["TEST_IMAGE"]; urllib.request.urlopen("http://127.0.0.1:8000",timeout=2)']
      interval: 2s
      timeout: 3s
      retries: 1
YAML
cat > "$testdir/scripts/verify.sh" <<'SH'
#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
"${COMPOSE[@]}" exec -T api python -c 'import urllib.request; assert urllib.request.urlopen("http://127.0.0.1:8000",timeout=2).status==200'
echo 'Isolated rollback service verified'
SH
chmod +x "$testdir/scripts/verify.sh"
docker compose --env-file "$testdir/.env" -f "$testdir/compose.yaml" up -d --no-deps --no-build --wait --wait-timeout 30 api
set +e
bash "$testdir/scripts/update.sh" "$bad" "$testdir/artifacts"
rc=$?
set -e
[[ $rc == 1 ]] || { echo "Expected failed deployment, got $rc" >&2; exit 1; }
cmp "$testdir/original" "$testdir/.env"
bash "$testdir/scripts/verify.sh"
echo 'PASS: real Docker health failure rolled back exact config in isolated project; no graph mounts or volumes used.'
