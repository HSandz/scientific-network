# AI Research Network Explorer (2021–2025)

A self-contained, local full-stack scientific knowledge graph exploration workspace for the **AAAI and IJCAI 2021–2025** cumulative release graph (`release-d3c788c3114a`, release v4).

The explorer connects **read-only** to the isolated `neo4j-five-year` Neo4j instance (`bolt://127.0.0.1:7689`) and cross-references local release ledgers (`reports/release-v4/analysis.json` and `data/processed/release-graph-v4/graph.json`) for full-projection network metrics, Louvain community partitions, `EvidenceRecord` provenance, and `AffiliationObservation` author–paper–organization triples.

Production operations: see [Azure runbook](../../ops/azure/README.md) for the
Cloudflare Pages + Azure/Caddy deployment, immutable SQLite evidence artifacts,
backup, restore and rollback. Local development commands below remain available.

---

## 1. Architecture & Technology Stack

### Frontend (`apps/research-explorer/frontend/`)
- **React 18 + TypeScript + Vite**
- **Sigma.js v3 + Graphology**: WebGL interactive network canvas with per-frame bounding-box label collision rejection, neighborhood highlighting, node dragging, and deterministic seeded layouts (`seeded`, `circular`, `concentric`).
- **Tailwind CSS + Lucide Icons**: Responsive `achromatic-ledger` workspace with neutral charcoal dark and warm stone light themes (`Geist` + `Geist Mono`), contextual entity/edge inspector, slide-over tablet/phone drawers, and full-width Table/Analytics views.
- **TanStack Query + Zustand**: API caching, request cancellation, URL state synchronization, theme persistence, selection history, and saved view bookmarks.
- **Apache ECharts**: Precomputed full-graph analytical charts linked to graph exploration with container `ResizeObserver` support.
- **Playwright**: End-to-end browser verification across desktop and mobile viewports.

### Backend (`apps/research-explorer/backend/`)
- **Python 3.12 + FastAPI + Pydantic v2**
- **Official Neo4j Python Driver (`neo4j`)**: Strictly read-only parameterized Cypher queries (`session.execute_read`) against `bolt://127.0.0.1:7689` with query timeouts and bounded limits.
- **Hybrid Artifact Store**: Instant lookup of full-graph centrality scores (`degree_strength`, `betweenness`, `pagerank`), Louvain communities (`community:00000`..`community:03014`), and `EvidenceRecord` / `AffiliationObservation` ledgers with automatic Neo4j fallback.

---

## 2. Five Exploration Modes

1. **Mode A — Researcher Collaboration (`COAUTHORED_WITH`)**
   - Undirected projection across **32,189** OpenAlex-resolved researchers and **80,482** accepted coauthorship edges (414 researcher isolates (no accepted coauthor edge)).
   - Filter by Louvain community, conference year range, venue (`AAAI` / `IJCAI`), minimum shared core papers, or minimum fractional weight.
2. **Mode B — Organization Collaboration (`COLLABORATED_WITH`)**
   - Undirected projection across **2,047** organizations and **13,031** inter-organization edges.
   - Filter by sector (`academia`, `industry`, `government`, `nonprofit`), cross-sector partnerships only, country code, or optional `CONTRIBUTES_TO_TOPIC` links.
3. **Mode C — Paper Citation Network (`CITES`)**
   - Directed core-paper citation graph (**7,308** within-corpus `CITES` edges across **6,315** connected core papers; 7,302 isolates with neither incoming nor outgoing in-corpus citations).
   - Preserves citing → cited arrow directionality and reports both within-corpus `in_degree` and `pagerank`.
4. **Mode D — Heterogeneous Knowledge Graph (All 5 Labels & 10 Predicates)**
   - Curated presets (`Topic Taxonomy Ecosystem`, `Bridge Researcher Ecosystem`, `Cross-Sector Organization Ecosystem`, `Top Cited Paper Ecosystem`) plus custom node-label and relationship-predicate toggles.
5. **Mode E — Evidence & Provenance Inspector**
   - Selecting any edge in the graph or table opens the provenance drawer displaying `evidence_kind` (`observed`, `inferred_topic`, `curated_taxonomy`, `derived`), `method_version`, `graph_version`, `EvidenceRecord` source URLs/SHA256/locators, supporting core papers, base edges, and aligned `AffiliationObservation` triples.

---

## 3. Prerequisites & Local Launch Commands

### 3.1 Verify `neo4j-five-year` is running
From the repository root (`/home/san/Code/scientific-network`):

```bash
docker compose ps neo4j-five-year
```

The service listens on:
- **Bolt**: `127.0.0.1:7689`
- **Neo4j Browser**: `http://127.0.0.1:7476`

> **Note on `.env`**: If the repository root `.env` sets `NEO4J_URI=bolt://localhost:7687` (used by the historical pilot service), `apps/research-explorer/backend/config.py` automatically targets `bolt://127.0.0.1:7689` unless `EXPLORER_NEO4J_URI` is explicitly overridden.

### 3.2 Start Both Backend and Frontend Together

```bash
./apps/research-explorer/scripts/dev.sh
```

Or run them in separate terminals from the repository root:

**Terminal 1 — FastAPI Backend (`http://127.0.0.1:8000`)**:
```bash
PYTHONPATH=apps/research-explorer:src uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Vite Frontend (`http://127.0.0.1:5173`)**:
```bash
npm --prefix apps/research-explorer/frontend run dev -- --host 127.0.0.1 --port 5173
```

Open **`http://127.0.0.1:5173`** in your browser.

---

## 4. API Overview

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Neo4j connectivity, graph version verification (`release-d3c788c3114a`), and artifact status |
| `GET` | `/api/graph/summary` | Node/edge inventory by label, predicate, and evidence class + quality gates & caveats |
| `GET` | `/api/graph/schema` | 5 entity labels, 10 predicates, and evidence classifications |
| `GET` | `/api/views` | Available projection modes and filter metadata |
| `GET` | `/api/views/{view}` | Bounded subgraph for `researchers`, `organizations`, `citations`, or `heterogeneous` |
| `GET` | `/api/search` | Global search across all 47,875 entities by name, title, DOI, OpenAlex ID, ROR, or ID |
| `GET` | `/api/nodes/{node_id}` | Full entity metadata, grouped incident relationships, and full-projection metrics |
| `GET` | `/api/nodes/{node_id}/neighbors` | 1-hop neighborhood expansion for any entity in the database |
| `GET` | `/api/edges/{edge_id}` | Relationship metadata and properties |
| `GET` | `/api/edges/{edge_id}/evidence` | Mode E provenance: `EvidenceRecord` items, supporting core papers, base edges, and `AffiliationObservation` triples |
| `GET` | `/api/analytics/overview` | Precomputed full-graph analytics from `reports/release-v4/analysis.json` |
| `POST` | `/api/paths` | Bounded shortest-path discovery (1–4 hops) across selectable traversal modes |
| `GET` | `/api/compare` | Side-by-side entity comparison (direct edges, shared papers, shared neighbors, topic portfolios) |
| `GET` | `/api/table/nodes` | Paginated, sortable node inventory table |
| `GET` | `/api/table/edges` | Paginated, sortable relationship table |

---

## 5. Testing Commands

### Backend Unit & Live Neo4j Integration Tests
```bash
PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -v
```

### Frontend TypeScript & Production Build Verification
```bash
npm --prefix apps/research-explorer/frontend run build
```

### End-to-End Playwright Browser Tests
With the backend (`127.0.0.1:8000`) and frontend (`127.0.0.1:5173`) running:
```bash
npx --prefix apps/research-explorer/frontend playwright test -c apps/research-explorer/frontend/playwright.config.ts
```

---

## 6. Scientific Integrity & Known Limitations

- **Read-Only Guarantee**: The application never mutates Neo4j data or modifies frozen release artifacts.
- **Displayed vs. Full-Projection Metrics**: The UI explicitly separates full-projection metrics (computed over all 32,189 researchers, 2,047 organizations, or 13,617 papers) from local displayed-subgraph degrees.
- **AI-Assessed Edge Precision**: Release v4 edge precision is **96.50%** (`193 / 200`, Wilson 95% CI: `92.95%–98.29%`, `1` incorrect, `6` unverifiable, `0` missing; point target `95.0%`, Wilson lower bound target `>90.0%`) under the frozen dual-agent audit (`edge-audit-v1`, `ai_agent_review`). Independent human annotation was not performed (`human_validation: not_performed`, `reviewer_independence: not_established`, `verified_course_accuracy: not_established`).
- **Affiliation Coverage Limit**: Author–paper affiliation resolution covers **73.71%** of authorship positions on OpenAlex-matched works (`48,259 / 65,469` matched authorship positions; `48,259 / 65,507 = 73.67%` across all official authorship positions; `48,259 / 50,437 = 95.68%` conditional on accepted authorships; `10,037 / 13,617` core papers have `>= 1` accepted `AFFILIATED_WITH` edge), missing the **80.0%** target (`FAIL`) due to upstream OpenAlex institution omissions (notably IJCAI 2022–2024).
- **Topic Coverage & Historical Reference Agreement**: `HAS_TOPIC` edges are embedding-inferred (`sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, tau `0.2708871364593506`, delta `0.02`, max 3 leaf topics), covering **85.00%** of core papers (`11,575 / 13,617`, `2,042` abstained; `PASS` against the **80.0%** coverage target). On the historical 50-paper AI-reference topic evaluation (`d040-topic-partial-overlap-v1`), topic-label precision is **68.63%** (`0.6863`, `FAIL` against the **95.0%** component precision target) and historical micro-F1 is **0.4667** (vs phrase-baseline micro-F1 **0.2301** and precision **92.86%** at `26.0%` test coverage).

Classifier provenance: model and calibration come from `reports/release-v4/graph-summary.json`; v4 preserves frozen topic predictions from the embedding stage. The v4 identity correction method is a separate processing stage and does not describe a new classifier or retuning.

## 7. Finding → chart → graph → evidence

Knowledge graph remains the default. Explore findings opens five analytical sections:
evidence sensitivity and top-20 bridge ranks; inferred topic evolution by
venue/year/family; components and frozen community profiles; sector mixing including
unknown; and annual metrics, complete CCDF, citation cohorts and pair persistence.
Charts have exact-value tables and keyboard actions. Entity actions open actual
bounded neighborhoods; topic cells open the matching paper/topic/year/venue slice.
Back to finding returns to the analytical section. Representative maps are bounded
illustrations, not probability samples or complete components.

Frozen full-projection results come from `reports/release-v4/analysis.json`.
[Explorer extension v1](../../reports/explorer-analysis-release-v1/README.md)
adds deterministic descriptive cohorts, persistence and component representatives
without changing v4. Historical strict filtering is distinct from the UI's repeated
collaboration filter: the latter applies support ≥2 to R7/R8 only and preserves
binary CITES/HAS_TOPIC facts. Aggregate weights retain full-period meanings when a
year/venue window requires at least one supporting paper in that window.

URL/saved-view schema v2 records filters, projection, layout, presentation edge
filter, selection and scope. Ego and Path requests reconstruct bounded graphs;
manual appended expansions are explicitly transient and share a safe filtered
overview with a notice. Bookmarks persist in localStorage; legacy URLs migrate.
Clipboard failures offer selectable text. JSON and separate node/edge CSV exports
contain precisely the effective displayed graph, including every semantic edge ID;
JSON adds view specification, timestamp, quality, methods and caveats. It is an
interchange artifact; arbitrary JSON import is not implemented.

Sigma/Graphology and ECharts instances persist through ordinary updates. Existing
node coordinates/camera survive selection and expansion. Parallel/reciprocal
relationships have distinct keyboard-selectable SVG lanes and source/target arrows.
Mixed-label node sizes are fixed; homogeneous sizes use their defined full-projection
metric. Camera/chart motion respects reduced-motion preferences. Missing release
metadata or analytics is Unavailable with Retry; counts/gate success are never
fabricated from defaults.

Full-period curated presets reject narrowed year/venue/topic requests with guidance
to select Researcher → Paper → Topic; they never silently ignore those constraints.
Curated ranking ties use stable IDs.

Current supported expansion preserves community/country/topic/cross-sector and
paper-window constraints, with bounded candidate selection and stale-request
protection. Comparison reports complete distinct shared/unique totals before
bounded previews, with source-paper traceability. Graph/Table/Analytics bookmarks
restore their workspace controls, including Table query/sort/page and analytical
section/filter state. Paths and comparisons explicitly use full-period data.

Unsupported narrowed heterogeneous presets reject requests; selected contextual
Ego centers may remain with zero matching links. Straight-edge evidence styles use
color; dash patterns are on parallel lanes. Node-size chooser and sustained
performance/accessibility certification remain incomplete. See the
[final integration and release plan](../../reports/explorer-final-integration-2026-11-10.md)
for exact validation, immutable package identities and production limitations.
