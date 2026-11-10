#!/usr/bin/env bash
# Offline Community dump. Brief maintenance window; graph data stays unchanged.
source "$(dirname "$0")/common.sh"
exec 9>"$AZURE_COMPOSE_DIR/.runtime.lock"
flock -n 9 || { echo 'Another deployment/maintenance operation is running.' >&2; exit 1; }
output=${1:?Usage: backup.sh /absolute/new-backup-directory}
[[ "$output" = /* && ! -e "$output" && ! -L "$output" ]]
(( $(df --output=avail -B1 / | tail -1) > 6 * 1024 * 1024 * 1024 )) || { echo 'Insufficient backup headroom.' >&2; exit 1; }
# Read only nonsecret volume configuration via Compose's structured model.
volume=$("${COMPOSE[@]}" config --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["volumes"]["neo4j-data"]["name"])')
"${COMPOSE[@]}" ps --status running --services | grep -qx neo4j || { echo 'Expected running production DB.' >&2; exit 1; }
api_running=$("${COMPOSE[@]}" ps --status running --services | grep -x api || true)
mkdir -m 700 "$output"
# Preserve SSH user ownership; UID 7474 writes in a dedicated subdirectory only.
mkdir -m 700 "$output/dump"
sudo -n chown 7474:7474 "$output/dump"
recover() {
  "${COMPOSE[@]}" up -d --wait --wait-timeout 180 neo4j
  if [[ "$api_running" == api ]]; then "${COMPOSE[@]}" up -d --wait --wait-timeout 120 api; fi
}
trap recover EXIT
"${COMPOSE[@]}" stop api neo4j
"${DOCKER[@]}" run --rm --network none --user 7474:7474 --memory 1g \
  -e HEAP_SIZE=512m -v "$volume:/data" -v "$output/dump:/backups" \
  neo4j:5.26.12-community neo4j-admin database dump neo4j --to-path=/backups
sudo -n chown -R "$(id -u):$(id -g)" "$output"
chmod 600 "$output/dump/neo4j.dump"
(cd "$output/dump" && sha256sum neo4j.dump > SHA256SUMS)
chmod 600 "$output/dump/SHA256SUMS"
echo "Backup created in $output/dump; copy it OFF the VM over SSH before treating it as durable."
