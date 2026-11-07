# WORK-2026-11-06-009 — Pregraph source closure and feasibility

| Field | Value |
| --- | --- |
| Status | partial — P01 remains incomplete; Site publication awaits approval |
| Recorded | 2026-11-06T23:56:19+07:00 |
| Finalized | 2026-11-07T00:45:28+07:00 |
| Work performed | 2026-11-06–07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-06-008](2026-11-06-008-pregraph-completion-plan.md) |
| Git state | main at 66e692d; extensive prior uncommitted changes preserved |

## Objective

Proceed from the completion plan's explicit P00/P01 next step: inventory and
protect the current source/config/sample state, verify official source and track
evidence, and perform bounded P02 feasibility work. Do not enrich papers, alter
frozen membership, acquire held-out content, build/import a graph, or change the
public Site audience.

## Changes and findings

- Captured the P00 starting inventory at base commit `66e692d0e96505ea72c53144c00c20651584cf2d`:
  **8,494 files / 2,675,898,980 bytes** across project source, configuration,
  historical artifacts, caches, tests, documentation and reports. Existing
  uncommitted work was preserved.
- Verified the official ICAPS 2025 call, topic policy and accepted-paper list.
  Its OJS issue has 52 records: 48 accepted main-research records now included,
  three accepted position records excluded under the existing policy, and one
  frontmatter record excluded. The correction is bound to input/page evidence in
  `data/manifests/five-year-source-corrections-v4.json` and recorded as D029.
- Added roster v6 as a new version. It retains all 170 edition candidates and
  reports 89 eligible, 41 unresolved and 40 unavailable editions. It contains
  88,608 observations: 85,850 included, 2,758 excluded, zero record review.
  Added the v6 config/parser/CLI dispatch and four focused synthetic tests.
  V1–v5 and all frozen diagnostic/pregraph inputs remain preserved.
- Checked official route leads for ICLR, MICCAI and AAMAS. None yielded a complete
  eligible roster or closed track/rights questions. P01 remains incomplete with
  **81 edition gaps**.
- P02 is a **no-go for broader enrichment**. The canonical work population,
  prospective P03 frame, current free-resource limits, storage budget and real
  reviewer capacity are not measured. No provider quota or research-service health
  check, paid spend, paper/PDF/model request, or annotation was made; the current
  broader-enrichment budget remains zero.
- Updated README/docs/status/roadmap/collection guidance, D029, and the local
  `reports/site-report.md`. The existing Site is active and public at v14 with its
  existing URL/audience. Local Report publication is pending approval, detailed
  below; no Site source or audience was changed.
- Measured evidence: [v6 recovery report](../../reports/five-year-source-recovery-v6.md),
  [v6 ledger](../../reports/five-year-edition-ledger-v6.csv), [route triage](../five-year-source-triage.md),
  and [P02 feasibility checkpoint](../../reports/five-year-pregraph-feasibility-v1.md).

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `UV_CACHE_DIR=/tmp/uv-cache-work009 uv run pytest tests/test_ojs_v6.py -q` | passed, exit 0; 4 tests | focused v6 contract test |
| `UV_CACHE_DIR=/tmp/uv-cache-work009 uv run pytest` | passed, exit 0; 181 tests in 4.07s | `reports/runs/WORK-2026-11-06-009/pytest.log` (ignored) |
| Source-disabled v6 CLI replay with `httpx.Client.get` forced to raise | expected exit 1; 89 eligible editions, 81 gaps, 88,608 observations, 85,850 included, 2,758 excluded, zero record review; no request escaped cache | `reports/runs/WORK-2026-11-06-009/v6-cli-replay.log` and `/v6-replay/summary.json` (ignored) |
| V6 artifact consistency | passed, exit 0; config, correction evidence, manifest, edition ledger and all output hashes match versioned metrics; zero network/enrichment requests recorded | `reports/runs/WORK-2026-11-06-009/artifact-consistency.json` (ignored) |
| Replay comparison | 26 output files compared; 14 byte-identical; the other 12 differ only in refreshed `checked_at` values and dependent hashes. After normalizing those values, no semantic differences remain. V5/v6 share 85,802 roster IDs; all 75,655 shared non-null prior assignment values match. | `reports/runs/WORK-2026-11-06-009/replay-parity.json` (ignored) |
| Protected-state hash recheck | 8,483 of 8,494 start files unchanged; eleven existing paths intentionally revised; no unexpected changed/missing prior file | `reports/runs/WORK-2026-11-06-009/protection-and-replay-check.json` (ignored) |
| `git diff --check` plus local link/whitespace check | passed, exit 0; ten Markdown files checked, no missing local links or whitespace defects; D029 anchor verified | terminal output; 10 changed/current Markdown files |
| P02 live quota/storage/service checks, enrichment, new sampling, held-out acquisition, graph/import | not run; no-go holds and these actions are outside the authorized boundary | none |

## Decisions

[D029](../decisions.md#d029--icaps-2025-roster-correction-and-enrichment-no-go-2026-11-07) records the ICAPS 2025 source disposition and P02 no-go. Existing scope, quality targets, schema and frozen samples remain in force.

## Open issues and limitations

P01 is still incomplete, the full pregraph gates remain false, and P02 has no
finite executable budget. The route leads for ICLR/MICCAI/AAMAS are not complete
rosters. Independent human source-policy review and reviewer capacity must not be
represented as completed. The v6 rerun refreshes `checked_at` fields, so its entire
output tree is not byte-identical despite semantic parity in the checked roster,
ledger, assignment and leakage content.

The Sites helper first failed because it was started in a nonempty `/tmp`
directory. Retried from a new empty workspace; the default sandbox could not
resolve the official source Git host. Escalated helper launch reached its hidden
stdin prompt, but automatic review rejected sending the unexpired bearer
credential through the outside-sandbox terminal, stating that general Site
refresh authorization did not authorize that credential transmission. No retry
or alternate credential path was attempted. The Site remains at v14; no v15
receipt exists. Request explicit approval before transmitting a short-lived
credential through that helper.

## Next step

Continue P01 by resolving the remaining 81 edition candidates with complete
official sources and track/rights evidence. Maintain the P02 no-go until a
canonical population, prospective P03 design, measured free-resource/storage
limits and actual reviewer hours provide a credible bounded budget. Preserve every
frozen assignment and the v2-bound diagnostic/pregraph bundle. Publish the local
Report update to the existing Site only after explicit approval for the credential
transmission required by its source workflow.

## Corrections

None.
