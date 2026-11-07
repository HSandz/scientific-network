# WORK-2026-11-07-004 — MICCAI official roster closure

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 09:09 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-003](2026-11-07-003-iclr-source-review.md) |
| Git state | main at 66e692d; extensive prior uncommitted work preserved |

## Objective

Continue P01 from the [pregraph completion plan](../pregraph-completion-plan.md)
by resolving the MICCAI editions supported by complete, locally captured official
rosters and reconciling the remaining year/count discrepancies. Keep scope, frozen
assignments, source-use boundaries and the P02 no-enrichment stop unchanged.

## Changes and findings

- Task opened from roster v8. Thirteen successful official HTML captures and the
  failed 2022 accepted-list route are recorded by hash in [source corrections v7](../../data/manifests/five-year-source-corrections-v7.json).
- Roster v9 adds MICCAI 2021 (531), 2023 (730) and 2025 (1,027), matching each
  captured official list to the Springer year-book full-paper count; the 2025
  Society final update also states 1,027 accepted papers. 2021/2023 roster entries
  have titles/IDs but no author bylines. The 2025 list includes BibTeX names; none
  of these names alone resolves a person or accepts a graph claim.
- MICCAI 2022 remains unresolved: accepted-list retrieval returned HTTP 522;
  Springer describes 574 full papers and its series index displays 576. MICCAI
  2024 remains unresolved: 856 Society-list records versus 857 accepted full
  papers. Springer index counts 535/576/732/857/1,029 are retained separately
  from year-book accepted/full-paper counts; no count difference was guessed away.
- V9 has 97 eligible editions / 10 no-edition findings / 23 unresolved
  roster/adapter editions / 40 access-unavailable editions. It contains 94,000
  observations: 90,499 included and 3,501 excluded. The 63 incomplete candidates
  keep P01 partial. All 76,629 guarded assignments, including 1,095 tests, remain
  guarded; no split, enrichment, held-out acquisition, graph or database action
  occurred.
- Full per-record roster files and raw captures remain ignored local data. The
  tracked correction stores source URLs, response hashes and aggregate counts;
  a clean checkout does not contain the captured HTML required to replay v9.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Required project/status/work-log/config/source-policy review | completed | `README.md`, `docs/project-plan.md`, `docs/graph-schema.md`, `docs/status.md`, `docs/work-log/README.md`, `docs/pregraph-completion-plan.md`, source triage, v8 ledger/config, D015, v9 config and source policy |
| `UV_CACHE_DIR=/tmp/uv-cache-work004 uv run pytest tests/test_miccai_rosters.py -q` | passed, exit 0; 5 passed | `tests/test_miccai_rosters.py`; synthetic list/BibTeX parser cases |
| MICCAI correction-contract load | first attempt failed before roster output because the generated correction lacked `edition_dispositions`; fixed manifest, then passed, exit 0; 13 captures / 5 dispositions validated | `_load_corrections` verifies the source set, hashes, list counts, Springer text/counts and held years |
| `UV_CACHE_DIR=/tmp/uv-cache-work004 uv run research-network discover --config configs/corpus-five-year-v9.yaml --output data/manifests/five-year-roster-v9 --cache data/raw/five-year-source-cache-v9` | expected partial-scope exit 1; 94,000 observations, 90,499 included, 97 eligible, 63 incomplete | v9 summary; manifest SHA-256 `381b0eade87bc8272b17e184eb27d2e5c773a41641eceb6a38ae6f964bff2b4b`; edition-ledger SHA-256 `b8139167f946aa7ae06a75bd4a4f23ff84fbef68ac3253685688295e2c9a6846` |
| V9 output and membership safeguards | passed; all 30 inherited non-MICCAI edition artifacts match the v8 hashes; 2,288 MICCAI IDs unique; 76,629 assignments / 1,095 tests guarded; no new split | v9 metrics and ignored `data/manifests/five-year-roster-v9/` output |
| Re-run of v9 `discover` command | expected exit 1; output hashes and roster/ledger counts match the first run | validated saved v9 checkpoint |
| `UV_CACHE_DIR=/tmp/uv-cache-work004 uv run pytest` | passed, exit 0; 198 passed | Full configured offline suite |
| Documentation relative-link integrity check | passed, exit 0; 324 relative targets resolved across 13 Markdown files | Included the final status, plan, roadmap, collection, decision, triage, report and work-log edits |
| `git diff --check` | passed, exit 0 | No whitespace errors in tracked diffs |
| Config/correction/ledger integrity | passed, exit 0; 13 source captures, five dispositions, 170 ledger rows and aggregate counts consistent | v9 config SHA binds correction manifest; report metrics and aggregate CSV match discovery summary |

## Decisions

[D032](../decisions.md#d032--miccai-roster-closure-and-unresolved-edition-counts-2026-11-07).
D022, D029–D032, the existing scope and track policy, all frozen assignments,
and the P02 no-go remain in force.

## Open issues and limitations

MICCAI 2022 and 2024 remain unresolved pending complete, reconciled official
record lists. Twenty-three roster/adapter editions and 40 access-unavailable
candidates still keep P01 incomplete. Publisher index counters are not treated as
accepted-paper counts. MICCAI 2021/2023 accepted lists lack bylines; D015 requires
authoritative detail bylines before work matching/core acceptance. Independent
semantic accuracy and release coverage remain unmeasured. Ignored raw captures
make the run a local replay rather than a clean-checkout replay.

## Next step

Continue P01 with the remaining source families, preserving the v9/v8 evidence
and all frozen assignments. Revisit MICCAI 2022/2024 only when complete official
record-level evidence can reconcile their counts; retain both as unresolved until
then. Keep P02 no-go for broader enrichment.

## Corrections

The documentation link check passed after the handoff updates. The dated
follow-up in WORK-003 records that later shared-documentation check without
rewriting WORK-003's original partial result.
