# Azure deployment — 10 November 2026

Status: fully deployed and functionally verified at 2026-11-10 15:02 +07:00. Work: WORK-2026-11-10-007. Graph: `release-d3c788c3114a`.

## Resource inventory and plan

Ubuntu 24.04.5 LTS (x86-64), Standard_B2als_v2, East Asia; 2 vCPUs,
3.8 GiB physical RAM. One 30 GB persistent OS disk, ext4 root, initially
27 GiB free; no temporary disk. Existing services are OS/Azure/SSH services.
Password SSH is disabled; key access and sudo work. Preserve SSH configuration.

4 GiB swap file on the OS disk, mode 0600, fstab `sw,nofail`, swappiness 10.
Azure-agent swap stays disabled; cloud-init is complete. No disk formatting.
Persistent graph volumes stay on the OS SSD. Neo4j maximum heap 768 MiB,
page cache 512 MiB, container memory 2 GiB; API maximum 768 MiB, one worker;
Caddy maximum 128 MiB. Swap protects transient spikes; measured use is recorded
below after workload validation.

## Preservation and integrity

Original dump stays outside Azure at the user-supplied backup path. Local and
transferred SHA-256: `1206b2572c4ebfb25b2c7db961daa429e0854d5daa14f307658ab178ecdce1df`.
The local source service is only queried read-only; it is never stopped or changed.
Render and Aura are preserved. Existing uncommitted migration reports are preserved.

A startup command was issued before the first loader fully returned; the new
server was immediately stopped. The first volume is retained unused. A clean
second restore completed before server startup; the final volume is
`scientific-network-production-neo4j-data-v2`. Scripts now lock maintenance and
require a completed restore marker. No overwrite flag or graph rebuild is used.

The original image seeded empty `databases`/`transactions` directories in the
first new volume; the initial guard refused them. Guard now permits only that
empty skeleton and rejects all actual data. The first local image build failed
because WSL's desktop registry credential helper was unavailable; an isolated
empty Docker config fixed public-image builds without touching user credentials.

## Runtime artifacts

EvidenceRecord and AffiliationObservation objects are stored in indexed,
read-only SQLite; the builder exhaustively roundtrip-checks every object.
Analysis retains base projections/first frozen communities and all release
metrics, robustness results and scientific caveats used by the API. Original
research artifacts remain unchanged. Exact analytics response, node-metric,
community membership and ranking parity passed locally.

## Database acceptance

Fresh local source inventory, restored Azure inventory, and post-backup/restart
Azure inventory match exactly. No scientific graph difference was found.

| Check | Measured result |
| --- | --- |
| Inventory | 47,875 nodes; 225,731 relationships; every label/predicate matches release v4 |
| Node labels | Researcher 32,189; Paper 13,617; Organization 2,047; Topic 20; Venue 2 |
| Relationships | AUTHORED 50,437; AFFILIATED_WITH 38,664; PUBLISHED_IN 13,617; CITES 7,308; HAS_TOPIC 14,222; SUBTOPIC_OF 16; COAUTHORED_WITH 80,482; COLLABORATED_WITH 13,031; RESEARCHES_TOPIC 5,622; CONTRIBUTES_TO_TOPIC 2,332 |
| Metadata | All nodes/edges retain graph version `release-d3c788c3114a`; project metadata unchanged |
| Schema | Five uniqueness constraints and seven indexes identical, all indexes ONLINE |
| Identity | All node IDs and edge IDs present and unique; deterministic samples match |
| Full typed node-property stream | `640d30984212dcde382ace154e19b275f9ccc0a24ac164f56a9872e3d476eea1` |
| Full typed relationship-property stream | `fd01fa8837824c5a207eb339d855e616acfad626a81b813c0256701fef2c2936` |

Fingerprints cover every label, stable ID, relationship type/direction, endpoint,
property value/type, weight, support count, evidence identifier and provenance
property. Schema comparison also includes deterministic names and online states.
Neo4j reports the scientific `neo4j` database `read-only/online`; its fresh system
database remains writable for DBMS authentication. No source database operation
beyond read-only queries occurred.

The SQLite ledger preserves 142,928 evidence objects and 56,273 aligned affiliation
observations, including repeated supports and their ordering. Original graph JSON
is not shipped or loaded into Python. [Artifact manifest](azure-runtime-artifacts-v1.json)
records input/output hashes; `verify.sh` checked every deployed artifact hash.

## Application and public cutover

- API: <https://scientific-network-api.eastasia.cloudapp.azure.com/api/health>;
  readiness `/api/ready` and liveness `/api/live` return HTTP 200.
- Frontend: <https://scientific-network-explorer.pages.dev>, unchanged project/URL.
  Pages production `VITE_API_BASE_URL` now targets Azure. Original and current
  environment variable key sets match. Build configuration and other projects
  were not changed. [Pages receipt](azure-pages-cutover-receipt-v1.json) records
  successful production deployment of implementation commit `ccdb690`.
- Served production JS contains the Azure API URL and no Render URL. Browser
  network capture confirms all API requests go to Azure. CSP permits the exact
  HTTPS origin, CORS permits only the Pages origin, and HTTP redirects to HTTPS.
- Caddy obtained a trusted Let's Encrypt certificate, valid 10 November 2026 to
  8 February 2027. Certificate state persists in named volumes; automatic renewal
  is configured. Actual renewal has not elapsed and was not forced.
- Only SSH and Caddy ports 80/443 are public. Port 8000 is loopback only;
  7474/7687 are closed/filtered externally. SSH remains key-only and operational;
  SSH/firewall/NSG rules were not changed. No paid Azure resource was created.

## Acceptance checks

| Check performed in this session | Result |
| --- | --- |
| `uv run pytest -q` | 508 passed, one existing empty-parameter skip |
| `PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -q` | 19 passed, including live source integration and four offline production guard tests |
| Offline CLI `uv run research-network schema` | passed; generated Cypher, no DB writes |
| Locked dependency export, local amd64 image build/import/layout check | passed; research/model dependencies excluded, required NumPy retained |
| TypeScript/Vite build with Azure API URL | passed locally and in Cloudflare production; existing large-chunk warning remains |
| Public API smoke suite | 28 checks passed in 18.193 seconds; graph modes, global/diacritic search, details, citations, neighborhoods, paths, comparison, analytics, tables, evidence/affiliations, safe invalid inputs |
| Production Playwright suites | five passed in 54.3 seconds against the real Pages + Azure endpoints |
| Separate browser network/console/mobile check | all API traffic Azure, seven graph canvases, zero console/page errors, zero HTTP errors, no 390px horizontal overflow |
| CORS/preflight/CSP/TLS/redirect | passed; allowed origin exact; invalid origin receives no permission; trusted HTTPS; HTTP 308 |
| Resource and recovery checks | all three services healthy, `unless-stopped`, Docker enabled, zero automatic restart/OOM loops |
| Offline backup / Neo4j recovery | passed; API and database stopped/recovered; post-restart full-content/schema comparison exact |
| API/Caddy restart and rollback entry point | passed; readiness, HTTPS and artifact hashes recovered; rollback to saved known-good v3 settings verified |
| Secrets scan | no configured local or production password in intended source/report files or VM container logs; VM secrets mode 0600 |

The production browser suites verify entity/edge evidence drawers, analytics and
scientific caveats, shortest paths, comparisons, neighbor visibility/Ego/Back,
zero-match filters, theme persistence, and tablet/phone drawers. Separate screenshots
were inspected. No missing or degraded application feature was observed.

## Measured resources

| Measurement | Observed |
| --- | --- |
| Backend idle RSS after warm-up | 152.7 MiB |
| RSS after global search / 150-neighbor expansion / analytics | 152.7 / 152.9 / 152.9 MiB |
| Backend peak in sampled API workload | 154.2 MiB; 159.4 MiB snapshot during full browser suites |
| Neo4j main JVM RSS during workload | about 0.95 GiB; sampled peak 989.7 MiB; high-water about 1.1 GiB |
| Available physical RAM | ≥1,855.7 MiB in the 50-sample workload capture; about 2.0 GiB after browser suites |
| Swap | 4 GiB configured; maximum observed use 28 KiB; no sustained swapping observed |
| CPU sample peaks | API 40.35%, Neo4j 152.45% (Docker percent: 100% = one vCPU); idle fractions below 1% |
| Warm VM request time (three requests per phase) | search 3.358s total; neighborhood 0.850s; analytics 0.030s |
| API startup after restart | 2.206s from Docker start to application-startup-complete log |
| Root disk after acceptance | 12 GiB used, 17 GiB available (41% used); graph/artifact data and quarantine included |

These are bounded deployment workloads, not a capacity benchmark or long-duration
load test. First cold global search was 6.973 seconds; subsequent queries were
faster. Neo4j health probes use short-lived additional Java processes inside its
memory/CPU budget. Physical RAM headroom was retained throughout measured work.

## Operations, backup and limitations

Runtime directory: `/opt/scientific-network/ops/azure`. Services: Neo4j
`neo4j:5.26.12-community`, API `scientific-network-api:azure-20261110-v3`, Caddy
`caddy:2.10.2-alpine`. API image ID:
`sha256:a52d5f79347fba8c61d9857682104fc130ada9c390ef8a585b05ff6c40fa2f51`.
Artifacts are mounted read-only from `/opt/scientific-network/artifacts/azure-20261110-v1`.

Fresh production backup: 85,380,680-byte `neo4j.dump`, SHA-256
`48c404ebda3ff465ed8dfe7aeab2d17f696b244b3f7535f255688cb14c90dc23`.
Its off-VM directory is
`/home/san/.local/share/scientific-network/backups/azure-production-20261110T075000Z/`
(mode 0700, files 0600); checksum verified after transfer. Compatible admin tooling
confirmed a ZSTD archive with 41 files / 534,495,232 uncompressed bytes. The original
migration dump also remains safely outside Azure. Newer dump size differs because
normal Neo4j checkpoint/transaction-log retention removes historical log bulk;
full scientific content remains fingerprint-identical.

Scripts cover first setup, guarded restore, immutable artifacts/images, safe update,
known-good rollback, full DB verification/comparison, logs/status, resource sampling,
API smoke and offline backup/recovery. Docker JSON logs rotate at 10 MiB × 3;
Neo4j bundled file-log rotation remains active. See [runbook](../../ops/azure/README.md).
A known-good v3 env snapshot is retained; earlier failed-image snapshots are not
recommended rollback targets. The unused first graph volume is retained separately;
no cleanup deletion was performed.

Limitations: no VM reboot was needed/performed; reboot activation is supported by
fstab, enabled Docker and restart policies, while actual reboot recovery remains
untested. Real certificate renewal and long-term stability are not yet observed.
Public requests share a bounded 180/minute proxy budget; this may need evidence-based
tuning under real demand. Backups were copied off-VM now; no unattended off-site
schedule/alerting service was added. Keep copying backups off-VM operationally.

Render and Aura remain intact. Azure is the current verified runtime, but retain
both old resources through an observation period and until the user explicitly
authorizes cleanup. No required external action or missing feature remains.

## Failures corrected during execution

In addition to the early restore sequencing and WSL helper issues above: first API
startup failed from repository-path assumptions; corrected image layout and added
an import check. A functional smoke check caught absent NumPy for NetworkX layouts;
retained the required locked dependency and added an image layout exercise. Caddy's
unconditional fallback initially won route ordering; exclusive `handle` blocks
fixed it. A smoke fixture requested page size 1 although the API minimum is 5;
corrected fixture and reran the full suite. Offline CLI `--output` was unsupported;
stdout redirection passed. A system-Python scan lacked `dotenv`; managed `uv run`
scan passed. Backup metadata inspection as UID 7474 could not read its intentionally
private backup mount; root read-only inspection passed, with an explicit isolated
hostname to avoid a harmless admin-tool hostname lookup warning. A default Python
HTTP user agent received a Pages 403; curl and the real browser passed. No failure
was counted as a successful verification.

Ignored raw evidence: `reports/runs/WORK-2026-11-10-007/`. The migration agent's
uncommitted files/shared-document hunks remain local and were excluded from commits.
