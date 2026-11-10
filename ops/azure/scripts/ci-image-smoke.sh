#!/usr/bin/env bash
# Start the real server without production data or network access to a database.
set -euo pipefail
image=${1:?Supply image}
name="azure-api-smoke-${GITHUB_RUN_ID:-$$}"
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT
docker run -d --name "$name" --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --tmpfs /tmp:size=32m \
  -e EXPLORER_PRODUCTION=true "$image"
for attempt in {1..30}; do
  if docker exec "$name" python -c 'import urllib.request; assert urllib.request.urlopen("http://127.0.0.1:8000/api/live",timeout=2).status==200' 2>/dev/null; then
    docker exec "$name" python -c 'import urllib.request,urllib.error
try:
 urllib.request.urlopen("http://127.0.0.1:8000/api/ready",timeout=5)
 raise SystemExit("Readiness must not pass without database/artifacts")
except urllib.error.HTTPError as e:
 assert e.code == 503'
    exit 0
  fi
  sleep 1
done
docker logs "$name"
exit 1
