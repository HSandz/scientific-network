# WORK-2026-11-08-025 — Release Phase 0: housekeeping

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-08 03:05 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 02:55–03:05 +07:00 (system clock) |
| Contributor | Claude (Claude Code), at the user's request |
| Related task | [WORK-2026-11-08-024](2026-11-08-024-release-plan-reset.md) |
| Git state | `main`; D040 documents committed as `537e907` before this phase; Phase 0 changes committed after this entry |

## Objective

Release-plan [Phase 0](../release-plan.md): define the isolated `neo4j-five-year`
service and create the three release configs, with the old services stopped.

## Changes and findings

- Old services: `scientific-network-neo4j-1`, `-neo4j-extended-1` and `-grobid-1` were
  already exited (about 20 min before this session; the user stopped them). Free RAM
  rose to 6.2 GiB. Swap is still full (4.0 GiB used), which is why the build must
  stream large tables (fallback table, "Memory pressure").
- [compose.yaml](../../compose.yaml): added `neo4j-five-year` (profile `five-year`,
  ports 7476/7689 on 127.0.0.1, heap 512m–1500m, 1G page cache, own data and log
  volumes, same healthcheck as `neo4j`). Not started in this phase.
- New configs: [release-v1.yaml](../../configs/release-v1.yaml) (scope, roster path
  and sha256, OpenAlex settings, matching thresholds, paths),
  [quality-release-v1.yaml](../../configs/quality-release-v1.yaml) (base quality
  config with the §2.4 audit section; `status: frozen`; `review_design:
  split_with_overlap`, 200 global / 10 per type / 50 overlap, seed 20261101) and
  [analysis-release-v1.yaml](../../configs/analysis-release-v1.yaml) (frozen, with
  `strict_evidence_filter: {minimum_support_count: 2}` under `robustness`).
- The audit keys `review_design`, `reviewer_ids`, `overlap_sample_size` and
  `course_point_estimate_must_exceed` are read by Phase 1 code that does not exist
  yet; today's `edge_audit` ignores them and still demands two reviewers per edge.
- Roster v10 sha256 matches the plan (`84ff8ca7…`); in-scope rows by venue-year match
  §8.1 and total 13,617.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `git status`, `uv sync --locked --group dev --extra analysis` | passed, exit 0 | working tree had only the D040 documents |
| `uv run pytest -q -p no:cacheprovider` (baseline) | passed, exit 0; 218 passed, 1 skipped | matches WORK-024 |
| `docker compose --profile five-year config -q` | passed, exit 0; services `neo4j`, `neo4j-five-year` | validates the new service; nothing started |
| `sha256sum` and venue-year count of roster v10 | passed; hash equals the pinned value; 13,617 in-scope rows | inline script |
| `uv run pytest -q -p no:cacheprovider` (after changes) | passed, exit 0; 224 passed, 1 skipped | new [tests/test_release_config.py](../../tests/test_release_config.py) adds 6 |
| Neo4j integration | not run: the service is defined, not started (Phase 4) | — |

## Decisions

[D040](../decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08)
defaults were used unchanged; the user had not amended them.

## Open issues and limitations

- `docs/team.md` still has TBD names and IDs; the user fills it in (needed for the
  report and for reviewer letters A/B).
- Seed 20261101 was copied from `quality.yaml`; it is recorded before any sampling.

## Next step

Phase 1: tooling fixes (validator indexes, labeled batched loader, receipt-lock
removal in `analyze` and `freeze-audit-sample`, split-with-overlap audit and review
sheet). Acceptance: `uv run pytest` passes with the §7 tests and the 10k-paper
validator timing is recorded.

## Corrections

None.
