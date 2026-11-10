#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
: "${1:?Usage: build-image.sh immutable-tag}"
# A tiny context excludes secrets, dumps, node_modules, research data and tests.
staging=$(mktemp -d)
trap 'rm -rf "$staging"' EXIT
mkdir -p "$staging/ops/azure" "$staging/apps/research-explorer/backend"
mkdir -p "$staging/docker-config"
cp ops/azure/Dockerfile.api ops/azure/requirements-api.txt "$staging/ops/azure/"
rsync -a --exclude=__pycache__ --exclude=tests apps/research-explorer/backend/ "$staging/apps/research-explorer/backend/"
# Public images need no registry credentials. Isolate config to avoid forwarding
# credentials or invoking a desktop credential helper from WSL.
DOCKER_CONFIG="$staging/docker-config" docker build --platform linux/amd64 -f "$staging/ops/azure/Dockerfile.api" -t "scientific-network-api:$1" "$staging"
docker run --rm --network none --entrypoint python "scientific-network-api:$1" -c 'from backend.main import app; import networkx as nx; assert app.title == "Scientific Network Explorer API"; assert len(nx.spring_layout(nx.path_graph(4), seed=42)) == 4'
