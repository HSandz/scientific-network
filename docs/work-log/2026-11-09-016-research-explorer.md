# WORK-2026-11-09-016 — Modern scientific network explorer application

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09 20:23 +07:00 (Asia/Bangkok) |
| Work performed | 9 November 2026 20:23–21:33 +07:00 |
| Contributor | Antigravity, at the user's request |
| Related task | WORK-2026-11-09-015 |
| Git state | Local working tree on `main` (`be0ad9f` / `fb2f0e7`) |

## Objective

Design, implement, test, and document a self-contained, local interactive scientific knowledge graph exploration web application under `apps/research-explorer/`, backed by the existing `neo4j-five-year` database (`bolt://127.0.0.1:7689`, release graph `release-d3c788c3114a`) and read-only evidence/analysis artifacts, without modifying frozen scientific outputs or publishing to any remote service.

## Changes and findings

- **Live Neo4j and artifact architecture verified**:
  - Confirmed `neo4j-five-year` (`bolt://127.0.0.1:7689`) contains the exact release v4 (`release-d3c788c3114a`) inventory: 47,875 domain nodes (`Researcher`: 32,189; `Paper`: 13,617; `Organization`: 2,047; `Topic`: 20; `Venue`: 2) and 225,731 accepted relationships across 10 schema predicates.
  - Identified that Neo4j stores node and relationship properties (`edge_id`, `evidence_kind`, `evidence_ids`, `method_version`, `graph_version`, `validation_status`, `support_count`, `fractional_weight`), while full `EvidenceRecord` items (`142,928` records) and `AffiliationObservation` author–paper–organization triples (`56,273` records) reside in `data/processed/release-graph-v4/graph.json`, and full-projection centrality scores and Louvain communities reside in `reports/release-v4/analysis.json`.
- **Implemented FastAPI read-only backend (`apps/research-explorer/backend/`)**:
  - Created `config.py`, `models/schemas.py`, `repositories/artifact_store.py`, `repositories/neo4j_repo.py`, `services/explorer_service.py`, `api/routes.py`, and `main.py`.
  - Enforced read-only Neo4j sessions (`session.execute_read`), parameterized Cypher queries with strict label/predicate allowlists, bounded query limits, security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`), and method restrictions (`GET`, `POST /api/paths`, `HEAD`, `OPTIONS` only).
  - Implemented 15 endpoints covering health/version verification, graph summary & schema, Modes A–D bounded subgraphs, global entity search across all 47,875 entities, node detail, 1-hop neighborhood expansion, Mode E edge evidence provenance, precomputed full-graph analytics, shortest-path discovery, entity comparison, and paginated node/edge tables.
- **Implemented React + TypeScript + Sigma.js + ECharts frontend (`apps/research-explorer/frontend/`)**:
  - Created responsive 3-panel workspace (`TopHeader`, `LeftSidebar`, `SigmaGraphCanvas`, `RightInspector`, `TableView`, `AnalyticsView`, `SearchCommandModal`, `PathFinderModal`, `CompareModal`, `CaveatsModal`).
  - Preserved all scientific caveats (96.50% AI-assessed edge precision with Wilson 95% CI 92.95%–98.29%, human validation not performed, 73.71% affiliation coverage `FAIL`, topic embedding micro-F1 0.4667 `FAIL`, and local vs. full-projection metric separation).
- **Added developer script and documentation**:
  - Created `apps/research-explorer/scripts/dev.sh`, `apps/research-explorer/.env.example`, and `apps/research-explorer/README.md`.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -v` | passed (exit 0); 14 passed (8 unit + 6 live Neo4j integration tests) in 7.33s | `apps/research-explorer/backend/tests/` |
| `npm --prefix apps/research-explorer/frontend run build` | passed (exit 0); `tsc -b && vite build` succeeded in 6.26s | `apps/research-explorer/frontend/dist/` |
| `npx --prefix apps/research-explorer/frontend playwright test -c apps/research-explorer/frontend/playwright.config.ts` | passed (exit 0); 3 E2E browser suites passed in 38.1s against live `127.0.0.1:5173` and `127.0.0.1:8000` | `apps/research-explorer/frontend/tests/explorer.spec.ts` |
| `uv run pytest` | passed (exit 0); 508 passed, 1 skipped | Full repository regression suite |

## Decisions

- **Hybrid Neo4j + Artifact Store Lookup**: Neo4j serves live graph queries, global search, neighborhood expansion, shortest paths, and paginated tables, while `ArtifactStore` indexes `reports/release-v4/analysis.json` for full-projection centrality/community metadata and `data/processed/release-graph-v4/graph.json` for full `EvidenceRecord` and `AffiliationObservation` provenance (with automatic Cypher fallback if `graph.json` is absent).

## Open issues and limitations

- Local development only: no remote deployment, no GitHub push, and no changes to the published ChatGPT Site or frozen release v4 scientific artifacts.
- Upstream scientific coverage and quality limits of release v4 remain unchanged and are surfaced in the UI (`73.71%` affiliation coverage `FAIL`, `0.4667` inferred topic F1 `FAIL`, AI-assessed edge precision `96.50%` without human annotation).

## Next step

Launch locally via `./apps/research-explorer/scripts/dev.sh` when interactive exploration is needed; supply team personal/course facts before any final course submission package rebuild.

## Corrections

None.
