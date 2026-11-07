# WORK-2026-11-08-022 — P01 CIKM 2025 browser source capture

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-08 01:20 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-08-021](2026-11-08-021-acmmm-2024-browser-source-review.md) |
| Git state | `main` at `66e692d`; extensive existing uncommitted work preserved |

## Objective

Continue P01 by testing whether the official CIKM 2025 accepted-paper and
proceedings pages can be captured through the connected browser after local DNS
failures. Close the edition only if every eligible track and the full proceedings
frame reconcile under existing source and reuse rules. Preserve roster v10 and
frozen assignments.

## Changes and findings

- Added [D039](../decisions.md#d039--cikm-2025-browser-source-audit-2026-11-08),
  [source-correction overlay v12](../../data/manifests/five-year-source-corrections-v12.json),
  [source triage](../five-year-source-triage.md#cikm-2025-browser-source-capture-work-022),
  the current [completion-plan checkpoint](../pregraph-completion-plan.md), and
  an aggregate-only [Report update](../../reports/site-report.md). No per-record
  IDs, titles, author metadata, or DOI rows were added to tracked files.
- The connected browser captured HTTP 200 responses and headers for the official
  accepted-paper page, proceedings page, and Full, Short, and Applied Research
  calls. Raw decoded responses remain in ignored
  `reports/runs/WORK-2026-11-08-022/`; body/header hashes are in source-corrections
  v12.
- The accepted page has 827 unique IDs across seven categories: 436 Full Research,
  185 Short Research, 93 Applied Research, 52 Resource, 37 Demo, 11 PhD Symposium,
  and 13 Industry Day. Full/Short are research-track candidates; the separate
  Applied call distinguishes it from the Research Track, but no new track policy
  decision was made.
- The official proceedings page has 852 unique ACM Digital Library links under
  one DOI collection. Normalized title comparison matches 789 accepted records;
  38 accepted titles and 63 publisher titles lack an exact cross-page title match.
  Exact title plus author-set comparison matches 697 accepted rows overall and
  531 Full/Short rows. Thirty additional nonexact-title rows have a unique exact
  byline candidate, but none was adjudicated. This does not establish a complete
  accepted-to-proceedings crosswalk.
- The Full and Short calls condition proceedings inclusion on author registration
  and on-site presentation. The captured pages show an all-rights-reserved footer
  but no metadata license or bulk-reuse authorization. CIKM 2025 remains
  `access_unavailable` in roster v10; no v11 was created.
- One reviewer is reported with unknown hours and no second independent reviewer
  confirmed. P02 remains no-go. No split, enrichment, paper PDF, graph or database
  operation occurred.
- `get_site` confirmed the existing public Site and audience at version 18 with
  the project ID and URL preserved. The supported helper received a fresh
  authorized credential through hidden stdin but failed before checkout with
  `Unable to prepare the Site.` No Site source audit, push, build, or publication
  occurred; the local Report update is not live.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Current handoff, completion plan, source policy, v10 config, source triage, and Git state | passed; exit 0 | `docs/status.md`, `docs/work-log/README.md`, `docs/pregraph-completion-plan.md`, `docs/five-year-source-triage.md`, `docs/source-policy.md`, v10 config and ledger; extensive pre-existing worktree changes preserved |
| Connected-browser GET of the official accepted, proceedings, Full Research, Short Research, and Applied Research pages | passed; all HTTP 200; five decoded response bodies and headers hash-bound | `data/manifests/five-year-source-corrections-v12.json`; ignored raw captures under `reports/runs/WORK-2026-11-08-022/` |
| `python reports/runs/WORK-2026-11-08-022/cikm2025_aggregate_audit.py` | passed; exit 0; 827 unique accepted IDs, 852 ACM links, 789 normalized title matches, 697 exact title/byline-set candidates overall and 531 for Full/Short | aggregate JSON `reports/runs/WORK-2026-11-08-022/cikm2025_aggregate_audit.json`, SHA-256 `68f541b5898014249d0fd1290d1510574bd4c4e7ec0a163affbf82279172baf0` |
| `python -m json.tool data/manifests/five-year-source-corrections-v12.json` | passed; exit 0 | source-correction v12 syntax |
| `python reports/runs/WORK-2026-11-08-022/verify_protected_hashes.py` | passed; exit 0; 42/42 v10 outputs, seven split inputs, 76,629 membership rows/hash, and 1,095 reserved tests verified; v12 inherits v11 and binds to the unchanged v10 config | `reports/runs/WORK-2026-11-08-022/protection_hash_audit.json` |
| Sites `get_site` for existing project | passed; active/public, version 18, existing project ID and URL retained | project `appgprj_6ae7698b8b2881919d49df2426c517a2` |
| Supported Sites source helper with fresh authorized credential | failed; exit 1, `Unable to prepare the Site.`; no checkout/source result returned | No source audit, push, build or publication; public Site remains v18 |
| Python tests and roster replay | not run; documentation/source audit only | No project code or roster output changed |

## Decisions

[D039](../decisions.md#d039--cikm-2025-browser-source-audit-2026-11-08) keeps CIKM 2025 unresolved. D022/D015, v10, all frozen assignments and the P02 no-go remain in force.

## Open issues and limitations

CIKM 2025 remains `access_unavailable`. Its accepted-page IDs do not completely reconcile
to the official proceedings records, its Applied Research disposition remains
open, and metadata reuse permission is not established. The existing public Site
remains v18 until a permitted Site source update is completed.

## Next step

Continue P01 with another permitted official source route. Reopen CIKM 2025 only
after a complete accepted-to-proceedings crosswalk, a documented Applied Research
disposition, and a source-use basis are established. Retry the Sites source helper
only after a concrete repair or evidence of infrastructure recovery. Preserve v10
and every frozen assignment; do not start broader enrichment while P02 remains
no-go.

## Corrections

None.
