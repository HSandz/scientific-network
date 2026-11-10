#!/usr/bin/env bash
# Offline load into a FRESH dedicated volume; never overwrite an existing database.
set -euo pipefail
source "$(dirname "$0")/common.sh"
exec 9>"$AZURE_COMPOSE_DIR/.runtime.lock"
flock -n 9 || { echo 'Another deployment/maintenance operation is running.' >&2; exit 1; }
archive=${1:?Usage: restore-neo4j.sh /absolute/path/neo4j.dump new-volume-name [trusted-sha256]}
volume=${2:?Set an explicit fresh production volume name}
expected_sha=${3:-1206b2572c4ebfb25b2c7db961daa429e0854d5daa14f307658ab178ecdce1df}
[[ "$expected_sha" =~ ^[0-9a-f]{64}$ ]] || { echo 'Invalid trusted checksum.' >&2; exit 1; }
if [[ -f .restore-complete && "$(cat .restore-complete)" == "$volume" ]]; then
  echo 'This volume was already restored; refusing replacement.' >&2; exit 1
fi
[[ "$archive" = /* && "$(basename "$archive")" == neo4j.dump && "$volume" == scientific-network-production-neo4j-data-* ]] || { echo 'Invalid archive or dedicated volume name.' >&2; exit 1; }
if [[ -z ${3:-} ]]; then [[ $(stat -c%s "$archive") = 409200612 ]]; fi
echo "$expected_sha  $archive" | sha256sum -c -
(( $(df --output=avail -B1 "$(dirname "$archive")" | tail -1) > 8 * 1024 * 1024 * 1024 )) || { echo 'Need 8 GiB free recovery headroom.' >&2; exit 1; }
if "${DOCKER[@]}" ps -q --filter "volume=$volume" | grep -q .; then
  echo 'Volume is in use. Stop and inspect it before offline maintenance.' >&2; exit 1
fi
"${DOCKER[@]}" volume create "$volume" >/dev/null
"${DOCKER[@]}" run --rm --network none --entrypoint sh --mount "type=volume,src=$volume,dst=/data,volume-nocopy" neo4j:5.26.12-community -ec '
  # The official image can seed two EMPTY directories when a volume is first
  # attached. Permit only those empty skeleton directories; never database files.
  test -z "$(find /data -mindepth 1 ! -path /data/databases ! -path /data/transactions -print -quit)" || { echo "Refusing nonempty production volume" >&2; exit 1; }
  chown 7474:7474 /data
  chmod 750 /data
'
# The ignored backup directory is owned by SSH user; expose only a staging copy,
# readable by neo4j UID. Original archive remains mode 0600 outside this mount.
staging=$(mktemp -d "$(dirname "$archive")/.load.XXXXXX")
trap 'rm -rf "$staging"' EXIT
chmod 755 "$staging"
cp "$archive" "$staging/neo4j.dump"
chmod 644 "$staging/neo4j.dump"
"${DOCKER[@]}" run --rm --network none --user 7474:7474 --memory 1g \
  -e HEAP_SIZE=512m -v "$volume:/data" -v "$staging:/backups:ro" \
  neo4j:5.26.12-community neo4j-admin database load neo4j --from-path=/backups
# No --overwrite-destination; a failed partial restore also requires inspection.
echo "Loaded dedicated volume $volume. Verify before API startup."
printf '%s\n' "$volume" > .restore-complete
