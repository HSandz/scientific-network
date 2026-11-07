# WORK-2026-11-06-002 — Start five-year official roster collection

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-06 15:04 +07:00 (Asia/Bangkok) |
| Finalized | 2026-11-06T15:24:55+07:00 |
| Work performed | 2026-11-06, live implementation/collection |
| Contributor | Codex |
| Related task | [WORK-2026-11-06-001](2026-11-06-001-five-year-execution-plan.md) |
| Git state | main, base 66e692d; prior planning edits preserved; no project commit/push |

## Objective

The user explicitly authorized collection based on the five-year plan. Start
E01–E03 with additive executable contracts, official rosters and honest source
availability. Preserve historical configs, memberships, data and graph snapshots.

## Changes and findings

- [D022](../decisions.md) supersedes D018's execution pause for staged collection.
  Updated contributor/current project instructions; historical planning registry
  and readiness CSV remain unchanged snapshots.
- New [roster-only config](../../configs/corpus-five-year-v1.yaml), catalog-routing
  adapters, immutable per-edition checkpoints and CLI dispatch. New five-year
  config cannot run historical downstream split/acquisition/graph commands.
- **73,714 official roster records** across all five years: 70,973 included,
  2,556 excluded, 185 review. Counts are not deduplicated canonical works.
- All **170** candidates retained: **67 verified_eligible, 51 unresolved,
  40 access_unavailable, 12 needs_review**. **65,523 included records** are in
  eligible editions. Automated contracts are not independent semantic review.
- New offline `reconcile-rosters` preserves all **14,909** historical assignments,
  including all **5,046** originals. Collected included records: **13,823** existing
  assignments retained, **57,149** pending prospective design, **one** version
  candidate quarantined. No canonical merges, fresh splits or new tests created.
- Complete JSONL/Parquet rosters and detailed triage ignored locally; small input
  signatures, summaries and source/edition ledger tracked. Raw downloads immutable
  and ignored. Unknown source/redistribution rights remain explicit.
- Added [workflow](../five-year-collection.md), [measured report](../../reports/five-year-collection-v1.md),
  [summary JSON](../../reports/five-year-collection-v1.json), and [170-row CSV](../../reports/five-year-edition-ledger-v1.csv).
  Updated status, roadmap, docs index, source policy, scope/plan and mutable Site report.
- Published existing public **Site v7**, same identity/URL/audience. New native
  progress table and report/CSV/JSON downloads; full 20-section Plan retained.
  Native explorer payload remains historical `pilot-topic-d512d7239923` (399/533).
  [Receipt](../reference/sites-collection-publication-2026-11-06.json),
  [Plan snapshot](../reference/sites-collection-plan-2026-11-06.md),
  [Report snapshot](../reference/sites-collection-report-2026-11-06.md).

## Verification

All commands ran from repository root unless a different directory is named.
Ignored console/artifacts: `reports/runs/WORK-2026-11-06-002/`.

| Command/check | Outcome / exit | Evidence |
| --- | --- | --- |
| Initial `uv run pytest -q` | 105 passed / 1 failed; exit 1; fully unresolved ledger exposed Parquet empty nested-struct limitation | `pytest-initial.txt` |
| Rerun after using lossless JSONL edition ledger | 106 passed; exit 0 | `pytest.txt` |
| Final `uv run pytest -q` after leakage-triage additions | **108 passed in 3.15s**, exit 0; invented offline fixtures only | `pytest-final.txt` |
| `uv run research-network schema` | exit 0 | `schema.json` |
| `uv run research-network discover --config configs/corpus-five-year-v1.yaml --output data/manifests/five-year-roster-v1 --cache data/raw/five-year-source-cache-v1` | exit **1**, intentional incomplete-edition result; all 170 ledger rows and 73,714 records saved | `discovery-v1.txt`; manifest summary |
| Same discovery command replay | exit **1**, identical summary/output hashes; no new source requests needed | `discovery-replay.txt`; `final-checks.json` |
| `uv run research-network reconcile-rosters --input data/manifests/five-year-roster-v1/corpus_manifest.jsonl --previous-manifest data/manifests/extended-corpus-v3/corpus_manifest.jsonl --previous-membership data/manifests/extended-splits-v3/membership.jsonl --output data/manifests/five-year-reconciliation-v1` | exit 0; preserved assignments; no new splits | `reconciliation.txt` |
| Same reconciliation command replay | exit 0; identical output | `reconciliation-replay.txt` |
| `uv run python reports/runs/WORK-2026-11-06-002/summarize-collection.py` | exit 0; per-year/series/status summary and CSV, matching source hashes | tracked measured report/JSON/CSV |
| Protected before/after hashes and legacy-subset equality | 5,673 of 5,675 original protected files unchanged; only mutable `reports/site-report.md` and work-log index intentionally changed. All historical configs/raw/splits/graphs/reports/finalized entries/reference snapshots unchanged; 5,046 assignments are exact subset of 14,909 | `protected-before.json`, `final-checks.json` |
| Synthetic cases | cross-year routes/publication dates, NeurIPS track changes, ACL page completeness, same-name/Unicode bylines, immutable resume/hash mismatch, DOI/title leakage guards, mixed held-out exposure and legacy command rejection passed | `tests/test_five_year_collection.py` |
| Site build in `/tmp/scientific-network-site-20261106` with recorded PANDOC binary | exit 0; **20 sections, 262 unique IDs, zero embedded documents**, 1,201,423 HTML bytes | `site-build-check.json` |
| Local browser at `http://127.0.0.1:8011/#report` | Native 399/533 explorer unchanged; new 73,714/67/65,523 progress; Plan/Report switching, 3 new downloads HTTP 200; 390px mobile has no document overflow; zero console errors | native Playwright tools; `final-checks.json` |
| Supported Sites helper push/package + native save/deploy | Site **v7 succeeded**; exact pushed source `7f185d54f6433721702bbeb7d7383902424525c2` | publication receipt |
| Post-publication browser | Live navigation succeeded. Follow-up evaluation/fetch stalled and its retained exec cell was cancelled; do not claim complete live interactive/download revalidation. Native deployment succeeded and local browser checks passed | `final-checks.json` |
| `git diff --check` | exit 0 | final shell check |
| Neo4j/OpenAlex/GROBID, cold parsing benchmarks, independent semantic audit | **Not run**; not required by official-roster stage | no new DB/API/PDF/graph/accuracy claim |

Build command:

```bash
PANDOC=/home/san/.cache/uv/archive-v0/WGuPJWVt0YVQCVdTXlt37/lib/python3.13/site-packages/pypandoc/files/pandoc \
python3 /tmp/scientific-network-site-20261106/build_site.py
```

Input/config/method hashes are in versioned manifest/triage summaries and
`reports/five-year-collection-v1.json`. The roster hash is
`7a039e31f6a83dc894d93a72e8160fb24603d71a1b02ca867f11e909e9a5dc68`;
config hash `9914ea3ca428047078ebe106d784ab8852f2761637fe43e8a52cf85cd14ba402`.

## Decisions

[D022](../decisions.md): authorized additive staged collection; preserve historical
versions, release gates and prospective sampling protections. No paid API/service
spend or automatic project Git push. Sites skill publication used the existing
public project as required by the repository workflow.

## Open issues and limitations

This is a **partial first roster collection**, not completion of E01–E03 or a
qualified five-year graph. NeurIPS 2025 has 40 unknown position-track records;
ECVA heading layout/year evidence and RSS official year evidence need correction;
KR track boundaries need review. Catalog access without an adapter and publisher
access failures remain unresolved/unavailable. Missing links are never treated as
proof of no edition. Source rights have not received a full independent review.

Title matching guards leakage without proving work identity. Alternate-title
versions need corroborating identifier review. Triage covers provisional records
from incomplete editions; it cannot authorize their enrichment. New contracts and
prospective design remain necessary. Historical graph accuracy is still unmeasured;
no five-year researcher/edge count exists. No API/service allowance benchmark or
clean-clone/remote Git access test was run.

Collection and replay jobs ended. Task-owned port-8011 preview stopped. No collection
runs are intentionally left in the background. Credentials stayed in memory/stdin.

## Next step

Use **new config/output versions** to review/fix NeurIPS 2025, ECVA, RSS and KR
edition/track gaps, reconcile cross-year identifiers/exposure, and freeze E04's
prospective diagnostic sampling design. Acceptance: eligible edition counts and
source evidence reconcile, old held-out versions stay protected, and only reviewed
membership enters a bounded five-year metadata/PDF batch. Keep 11 November deadline
cutoffs and independent review/report time; do not lower release gates.

## Corrections

None.

### Checkpoint history

### Checkpoint — 2026-11-06 15:12 +07:00

- D022 recorded; additive roster-only config and CLI dispatch implemented. Historical
  split/acquisition commands explicitly reject this config.
- Offline suite: initial 105 passed / one failure exposed a Parquet empty-struct
  issue for fully unresolved ledgers. Fixed by retaining the heterogeneous ledger
  as lossless JSONL. Rerun: 106 passed in 3.14s; schema CLI exit 0.
- Collection running in exec session 27851; inspect
  `reports/runs/WORK-2026-11-06-002/discovery-v1.txt`. Current checkpoints include
  all five ICML years; NeurIPS 2025 retains 40 unknown position-track records for
  review rather than assuming main-track eligibility.
- Site source opened with the supported helper; publication pending finalized counts.
