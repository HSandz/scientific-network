# Azure production operations

Cloudflare Pages serves the existing React frontend. Caddy on the existing Azure
VM terminates public HTTPS and forwards `/api/*` to one FastAPI worker. FastAPI
queries Neo4j Community 5.26.12 over an internal Docker network and reads immutable
runtime artifacts. No pipeline, model, registry, paid resource or Aura/Render
runtime is required. Neither former service is deleted.

Public frontend: <https://scientific-network-explorer.pages.dev>.
API hostname: `scientific-network-api.eastasia.cloudapp.azure.com`.
VM access: `ssh azure_scientific-network`.
Runtime directory: `/opt/scientific-network/ops/azure`.

## Resource and security boundaries

The inspected VM is Ubuntu 24.04.5 LTS, x86-64, 2 vCPUs, 3.8 GiB RAM, one 30 GB
persistent OS SSD, no temporary resource disk. A 4 GiB mode-0600 OS-disk swap file
is activated by fstab with `nofail`; swappiness is 10. Azure-agent swap remains
disabled. Never format an unrecognized disk or move graph data to temporary disk.

Neo4j: 512–768 MiB heap, 512 MiB page cache, 2 GiB container limit, 256 MiB
aggregate transaction budget, 15-second default transaction timeout. API:
768 MiB, one Uvicorn worker, at most 12 concurrent connections, eight Bolt
connections, 12-second query timeout. Caddy: 128 MiB, `GOMAXPROCS=2` to bound Go
runtime concurrency and leave room under its PID limit for health checks even
when the container sees the host's larger CPU inventory. Swap is protection for short
spikes, not additional physical RAM. Watch `vmstat` for sustained swap I/O.

Only Caddy publishes public ports 80/443. API port 8000 binds VM loopback for
operations; no public Bolt/Browser port exists, and Neo4j HTTP is disabled.
The database defaults to read-only. Community lacks Enterprise fine-grained
role controls; the API account is therefore protected by database read-only mode,
network isolation and parameterized read queries. The Compose control plane and
Docker access are privileged; `.env` must be 0600. API runs as UID 10001 with a
read-only root, no capabilities and no new privileges.

The API intentionally publishes accepted researcher, paper, institution, topic and
venue metadata, public scholarly identifiers, evidence excerpts, source URLs,
raw affiliation strings and aligned affiliation observations. It has no user
accounts, uploads, generic Cypher execution or write API. Existing source rights,
coverage limitations and AI-assessment caveats still apply. No private raw source
corpus is shipped. Evidence source locators can include research artifact paths;
these are provenance identifiers and do not grant filesystem access.

CORS permits only `https://scientific-network-explorer.pages.dev`, without
credentials. CORS is not authentication. Production docs/schema routes are disabled.
Only POST `/api/paths` is allowed; bodies are limited to 4 KiB, query strings to
8 KiB, parameters are bounded, and rate-limit state is bounded to 4,096 clients.
The proxy is not trusted for forwarded IP headers: requests share a conservative
180/minute API budget when arriving through Caddy. This is a small-site capacity
limit and may require tuning from observed demand. Spoofed forwarding headers
cannot evade it. Caddy enforces request-body and upstream response timeouts.
Frontend CSP explicitly allows only the production API origin plus its font hosts.

## First deployment

From the development checkout, use the existing SSH alias; never copy private keys.
Read the current work receipt before repeating setup. The original verified dump
must stay outside the VM:

```
/home/san/.local/share/scientific-network/backups/neo4j-five-year-aura-migration-20261110T035914Z/neo4j.dump
```

Size: 409,200,612 bytes. SHA-256:
`1206b2572c4ebfb25b2c7db961daa429e0854d5daa14f307658ab178ecdce1df`.

1. Inspect VM disk/memory, `/etc/fstab`, Azure-agent/cloud-init swap and existing
   services. `scripts/bootstrap-vm.sh` is for this inspected Ubuntu layout: it
   preserves existing swap, refuses an existing inactive swap path, needs >18 GiB
   free before creating 4 GiB swap, and installs official Docker CE only if absent.
   It never changes SSH or formats disks. Run remotely as the sudo-capable SSH user.
2. Locally run `uv sync --locked --group dev --extra analysis --extra report`.
   Build a new artifact version and image:

   ```bash
   uv run python ops/azure/scripts/prepare-artifacts.py --root . --output /absolute/new/artifact-directory
   ops/azure/scripts/build-image.sh immutable-release-tag
   docker save scientific-network-api:immutable-release-tag | gzip -1 | ssh azure_scientific-network 'sudo -n docker load'
   ```

   The API requirement file is hash-pinned from `uv.lock`, excluding research-only
   dependencies. Regenerate with:

   ```bash
   uv export --locked --no-dev --no-emit-project --prune beautifulsoup4 --prune httpx --prune pyarrow --no-annotate --no-header --output-file ops/azure/requirements-api.txt
   ```

   Build context includes only backend source and requirements. It excludes secrets,
   artifacts, tests, node_modules and papers. Public-image builds use an isolated
   Docker config to avoid WSL desktop credential-helper failures. Build for amd64.
3. Create `/opt/scientific-network/{ops/azure,backups,artifacts}` on VM. Copy this
   directory (excluding `.env`), the versioned artifact directory and the verified
   dump over `rsync`/SSH. Make backups directory 0700 and dump 0600. Verify hashes
   on both sides. Keep ≥8 GiB free for restore/recovery; never use the local graph
   volume or development Compose on the VM.
4. Create VM `.env` from `.env.example`, mode 0600. Generate a NEW production-only
   password with Python `secrets.token_urlsafe(36)` directly on the VM. Do not put
   it in shell history, output, Git or chat. Set immutable API/artifact versions
   and an unused `scientific-network-production-neo4j-data-*` volume name.
5. Run the guarded offline restore on VM:

   ```bash
   cd /opt/scientific-network/ops/azure
   scripts/restore-neo4j.sh /opt/scientific-network/backups/neo4j.dump scientific-network-production-neo4j-data-v2
   # Wait for successful exit and .restore-complete before starting Neo4j.
   sudo docker compose up -d --wait --wait-timeout 180 neo4j
   scripts/verify-database.sh > /opt/scientific-network/backups/azure-inventory.json
   ```

   Restore refuses a running/nonempty database and uses `neo4j-admin database load`
   as UID 7474 in the exact compatible Community image, without overwrite. It accepts
   only the official image's two empty skeleton directories. Maintenance scripts
   use `flock`; never bypass the lock by starting containers during a restore.
6. Copy inventory to development machine and compare against a fresh read-only
   local baseline using `scripts/compare-inventories.py source.json azure.json`.
   This compares full typed-property SHA-256 streams, stable IDs, labels,
   directions, all properties, deterministic samples, constraints and online indexes.
   Stop if it differs. Verification overrides only its own transaction timeout
   (300 seconds), not the public API timeout. It streams properties without loading
   the graph into Python. Keep the complete JSON baseline outside public Git.
7. Run `scripts/deploy.sh` only after verification. Caddy automatically obtains
   trusted certificates; DNS must resolve to this VM and Azure NSG must allow
   inbound TCP 80/443. Keep SSH access intact; do not open 8000/7474/7687.
   Run `scripts/smoke-api.py --base-url https://scientific-network-api.eastasia.cloudapp.azure.com/api`
   from outside Azure before frontend cutover.
8. In existing Pages project `scientific-network-explorer`, set production
   `VITE_API_BASE_URL=https://scientific-network-api.eastasia.cloudapp.azure.com/api`.
   Trigger a production build from tested source. It is a build-time Vite value;
   changing it alone does not update already-built JavaScript. Preserve all other
   Cloudflare projects/settings. Check compiled JS, CORS/CSP and browser flows.

## Runtime artifacts and integrity

`prepare-artifacts.py` never changes frozen research results. It creates an indexed
SQLite evidence/affiliation ledger, verifies every object by roundtrip, records
source/output SHA-256 values and refuses an existing output directory. The runtime
analysis retains all API-used base projection values and the first frozen Louvain
partition, plus release metrics, quality results and caveats. The unused strict
projection internals and additional community runs stay in original local artifacts.
API analytics, metrics and community/ranking parity are checked against originals.

Keep image and artifact directories versioned and immutable while running: SQLite
uses `mode=ro&immutable=1`. Never update a mounted database in place. Missing configured
SQLite fails startup; readiness requires all eight data inputs, graph inventory
verification and a fresh `RETURN 1` connectivity probe. `/api/live` tests the process;
`/api/health` retains the existing detailed API contract and refreshes inventory.
`verify.sh` also verifies every artifact hash. Counts alone are insufficient; run
the full fingerprint comparator after restores, graph changes or suspected corruption.

## Updates and rollback

Build and test locally, copy new image and versioned artifacts, then on VM:

```bash
cd /opt/scientific-network/ops/azure
scripts/update.sh scientific-network-api:new-tested-tag /opt/scientific-network/artifacts/new-version
scripts/status.sh
scripts/logs.sh api
# If verification fails, select the precise preceding ignored env snapshot:
scripts/rollback.sh .env.rollback-UTCSTAMP
```

Updates preserve the database volume; do not run `down -v`, remove volumes, or
reimport CSV. Keep preceding images/artifacts until rollback validation. A database
recovery loads the retained dump into a NEW volume, verifies it, and switches
`NEO4J_DATA_VOLUME`; never overwrite the failed copy. For a newer backup, supply
its independently verified SHA-256 as the restore script's third argument (the
default checksum/size are intentionally fixed to the original migration dump). Certificates persist in named
Caddy volumes. Restore system credentials from the protected VM secrets backup or
use a new password with a fresh restored system database; never commit credentials.

## Status, logs and resources

```bash
ssh azure_scientific-network
cd /opt/scientific-network/ops/azure
sudo docker compose --profile https ps
sudo docker compose --profile https logs --tail=100
sudo docker stats
free -h
swapon --show
df -h
scripts/status.sh
scripts/monitor.sh
scripts/logs.sh caddy
scripts/verify.sh
```

Docker JSON logs rotate at 10 MiB × 3 files/service. Neo4j file logs use its bundled
rotation policy; inspect volume sizes periodically. Health checks and restart
policies do not restart a merely unhealthy container: investigate its cause.
`unless-stopped` plus enabled Docker service restores running containers after a
VM reboot. fstab reactivates OS-disk swap. A reboot is not required for installation;
after any controlled reboot recheck SSH, swap, all health checks and public HTTPS.

## Backup and recovery

The original verified dump remains outside Azure. For a fresh offline Community
backup (brief API maintenance window):

```bash
ssh azure_scientific-network
cd /opt/scientific-network/ops/azure
scripts/backup.sh /opt/scientific-network/backups/new-UTCSTAMP
```

The script locks maintenance, checks disk headroom, stops API/Neo4j, writes a dump
as the Neo4j UID, records SHA-256 and recovers previously running services even
on failure. Caddy stays up and may return 503 during maintenance. Copy this new
backup and hash OFF the VM over SSH, verify it there, and retain a separately
protected copy of runtime `.env` and version manifests. Do not commit them. A dump
on the same 30 GB SSD is not a durable backup. No unattended external backup or
paid backup service is configured; schedule operator-controlled copies as needed.

Before retiring Render/Aura: verify browser flows, database fingerprints, a fresh
off-VM backup, HTTPS/certificate renewal and an observation period. Deletion still
requires explicit user authorization; this deployment never performs that cleanup.
