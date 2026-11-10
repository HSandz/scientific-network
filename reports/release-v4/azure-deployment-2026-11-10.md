# Azure deployment — 10 November 2026

Status: in progress. Work: WORK-2026-11-10-007. Graph: `release-d3c788c3114a`.

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

## Checks and deployment receipt

Pending; final measurements, HTTPS, database fingerprints and application results
will be added before this session closes. See ignored run artifacts under
`reports/runs/WORK-2026-11-10-007/` and [runbook](../../ops/azure/README.md).
