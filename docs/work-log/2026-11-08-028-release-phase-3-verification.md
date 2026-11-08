# WORK-2026-11-08-028 — Release Phase 3 graph verification

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-08 11:51 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 11:42–11:51 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-2026-11-08-027](2026-11-08-027-release-phase-2-openalex-acquisition.md) |
| Git state | `main` at `95c3029`; Phase 3 checkpoint changes ready for local commit |

## Objective

Verify the interrupted Phase 3 graph against the current D040 builder and complete the
Phase 3 exit criteria. Preserve the previous graph, record true measured coverage, and
check whether Phase 4's isolated Neo4j service can run in this environment.

## Changes and findings

- Fixed authorship review accounting in [release.py](../../src/scientific_network/resolve/release.py):
  paper-level authorship withholding now lists every affected byline position and
  counts each withheld position under a reason. Bumped the method version to
  `release-openalex-graph-v1.1` because the committed authorship rule changed the graph.
- The tracked graph summary now reports all four size gates with observed values and
  thresholds. Added regression tests for paper-level and duplicate-ID position queues.
- Rebuilt and promoted the graph to `data/processed/release-graph-v1/`; the prior
  ignored graph is preserved at `reports/runs/WORK-2026-11-08-028/previous-release-graph-v1/`.
  The tracked [graph summary](../../reports/release-v1/graph-summary.json) binds graph
  `release-4c1253e05f2c` to works sha256
  `2b7f3bc15ad46398e9f55ece060536050215238355e9580d2689f00005f55047`, release config
  `40c8461a1ddd426e02b4cb10d2260fc4a98b4c4638e7abfc53f8860f4aedb5eb`, taxonomy
  `dadd9ddc125a8aca4c4d8c9ca408a5d1493934ab0630fce9b790b191c5bebe2d`, and quality
  config `66945c3ec8e2efc13cbd9234ac2d9417f60e3fda93076a6dbe43c02606e0239f`.
- Resource snapshot: 32 CPUs, 11 GiB RAM (7.5 GiB available), 784 GiB free disk.
  Docker Desktop's executable is visible from WSL, but it reports that Docker cannot be
  found in this WSL 2 distro; no listener is available on port 7689.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis` | passed, exit 0 | locked dependencies unchanged |
| `uv run pytest -q -p no:cacheprovider` | passed, exit 0; 345 passed, 1 skipped | skip is the existing empty parameter set in `tests/test_cli.py` |
| `uv run research-network release-graph --config configs/release-v1.yaml --output-dir <fresh-run-dir> --summary <fresh-summary>` | passed, exit 0; 36.73 s, max RSS 2,452,812 KiB | final graph output under ignored `reports/runs/WORK-2026-11-08-028/final-c/` |
| `uv run research-network validate --input reports/runs/WORK-2026-11-08-028/final-c/graph/graph.json --config configs/quality-release-v1.yaml --require-size --output reports/runs/WORK-2026-11-08-028/final-validation.json` | passed, exit 0; structural errors `[]`; all size checks passed | validation binds graph sha256 `570fb4bb5b180cea30be2c7b942aeff1f2f0aef09874a29e33dcbf78334ab761` |
| Two same-input graph builds | semantic graph content matched after normalizing build-time `retrieved_at` on taxonomy evidence; normalized sha256 `b24b3bfab768bac3217bc8889b82f2b82725a221bfd822ec06fd8fd70fb99015` | raw byte hashes differ only because taxonomy evidence records build-time retrieval; graph version and all other graph fields match |
| Summary graph hash vs promoted graph | passed | `graph_sha256` matches promoted `graph.json` |
| `git diff --check` | passed, exit 0 | clean whitespace check |
| `docker info --format '{{.ServerVersion}}'` | failed, exit 1: Docker Desktop says CLI unavailable in WSL 2 distro | Phase 4 not run; port 7689 is not listening |

## Measured graph results

- 52,415 nodes, 261,755 edges, 13,617 core papers, 36,680 resolved core researchers.
- All ten relations are nonempty. R1–R4 contain 124,619 unique factual edges; derived
  edges: 130,829; inferred-topic edges: 6,291; curated taxonomy edges: 16. All four
  configured node/researcher/factual-edge/relation-type size gates passed.
- 59,159 of 65,469 author positions were accepted. 6,310 were withheld: 6,283 lack an
  OpenAlex author ID, 7 have incompatible names, 18 are on duplicate-ID papers, and 2
  otherwise compatible positions are withheld by the multiple-name-mismatch rule.
  Name-incompatible positions are 0.011% of the official positions; missing IDs are a
  separate coverage limitation. Five papers had all authorships withheld.
- 56,633 accepted author–paper positions have institution support (95.73% of accepted
  authorships). Eleven works remain unmatched/review; 147 paper-level copied-affiliation
  patterns are withheld. All three figures are counts, not semantic validation.
- Abstracts are present for 13,606/13,617 papers (99.92%). The unvalidated phrase
  baseline labels 5,198/13,617 papers (38.17%); 8,419 abstain. This is below the later
  topic-coverage target and is the reason Phase 5 remains necessary.
- Citation scan: 378,360 reference targets; 370,831 out of scope, 34 self-references,
  zero ambiguous target mappings; 7,308 unique in-scope citation edges.
- Independent accuracy/recall and reviewer agreement were not measured. Structural
  validation does not certify semantic accuracy.

## Decisions

No change to D040 scope or graph semantics. Method version is now v1.1 to distinguish
the current authorship behavior from the earlier stale artifact.

## Open issues and limitations

Phase 4 cannot start until Docker Desktop WSL integration is enabled. The existing
release graph passes Phase 3 only; it is not yet loaded or checked in Neo4j. Topic labels
are phrase-baseline predictions, not evaluated labels. No human edge audit has run.

## Next step

Phase 4: enable Docker Desktop WSL integration, start only `neo4j-five-year`, load this
versioned graph, run inventory/integrity queries, and verify idempotent replay.

## Corrections

None.
