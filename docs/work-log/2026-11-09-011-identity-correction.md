# WORK-2026-11-09-011 — Versioned ORCID identity correction

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09 15:18 +07:00 (Asia/Bangkok) |
| Work performed | 9 November 2026 |
| Contributor | Codex |
| Related task | WORK-010; full remediation B |
| Git state | main after 68191be; only task changes |

## Objective

Correct complete matched-source ORCID handling in a separately versioned graph, preserving immutable graph v3, topics and historical failed outcomes.

## Changes and findings

- [D040 amendment](../correction-amendment-2026-11-09.md) records explicit user authorization and pre-draw seed 20261109. New protocol/config paths selected before correction/sampling.
- Added global source-evidence collector, versioned resolver, explicit correction CLI and regressions. Strict whole-value/checksum checks found no malformed IDs in the actual source.
- Graph `release-d3c788c3114a`, SHA256 `6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`: 47,875 nodes / 225,731 edges; 32,189 researchers; 110,026 unique factual edges; all 10 relations nonempty. Full source has 4,492 conflicting IDs; 4,491 previously accepted researcher nodes and 49 unsupported organizations removed; 8,722 authorships removed. All core papers retained.
- [Summary](../../reports/release-v4/graph-summary.json) and [content freeze](../../reports/release-v4/content-freeze-v4.json) bind immutable inputs. Full diff (including support/weights, observations, evidence and additive authorless-paper reasons) is ignored under `data/processed/release-graph-v4/`; manifest hash is tracked in summary. Predictions/taxonomy/publication/citation claims and nonderived evidence have equal canonical hashes.
- New edge-only provenance scorer and complete raw source extractor are implemented; packet source verification rejects projected/changed authorship objects including omitted arrays. New analysis captions accurately distinguish AI assessment from absent human validation.

## Verification

| Check | Outcome |
| --- | --- |
| `uv run pytest` (run log) | 492 passed/1 existing skip, exit 0, 23.70s before later ADJ tests |
| Final integrated suite (separate coding context) | 504 passed/1 existing skip, exit 0, 26.74s |
| Focused identity/scorer/source tests | 59 identity, 74 scorer+combined, 1 raw-source test passed |
| `correct-release-identity` with all explicit input/output paths (see reproduction instructions) | exit 0; unused v4 graph, summary and content freeze produced; structural/taxonomy/size gates passed |
| Canonical invariant checks and 125 historical byte hashes | passed; no inference/reacquisition |
| Isolated service start/identity | healthy neo4j-five-year, 7689/7476, Neo4j5.26.12 Community; old graph present before reset |

Initial in-flight suite recorded 490 passed/2 new identity test failures/1 skip; corrected additive-reason handling and meaningful support-delta fixture, then all pass. Initial Docker log redirection failed because run directory absent; created before retry. A system-python Neo4j inspection lacked dependency; repeated through locked uv environment. No DB mutation in this checkpoint. Run artifacts under `reports/runs/WORK-2026-11-09-011/`.

## Decisions

Bounded amendment in decisions.md; missing ORCID allowed, malformed nonempty evidence withheld conservatively; unsupported organizations removed, all substantive paper metadata/denominators preserved; validator requires a new explicit reason on newly zero-authorship papers, so a narrow additive bookkeeping exception is bound before execution. Protocol finalization also adds explicit numeric_gate_scope for the new edge-only scorer.

## Open issues and limitations

No external actions authorized. Semantic accuracy requires new prospective source audit, not structural checks alone.

## Next step

WORK-012: verified isolated DB reset/import/replay and recomputed analysis; then prospective evaluator freeze.

## Corrections

None.
