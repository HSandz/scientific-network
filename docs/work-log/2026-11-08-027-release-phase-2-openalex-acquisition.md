# WORK-2026-11-08-027 — Release Phase 2: OpenAlex acquisition

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-08 03:40 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 03:20–03:40 +07:00 (system clock) |
| Contributor | Claude (Claude Code), at the user's request |
| Related task | [WORK-2026-11-08-026](2026-11-08-026-release-phase-1-tooling.md) |
| Git state | `main` at `8f55c06` at start; committed after this entry together with the Phase 3 builder, which is written and unit-tested but not yet run on real data |

## Objective

Release-plan [Phase 2](../release-plan.md): derive DOIs for the 13,617 roster papers,
fetch the matching OpenAlex works through `SourceCache`, apply the work-match rule,
and write `data/interim/release-v1/works.jsonl` and
`reports/release-v1/acquisition.json`. Exit (CP1): match rate reported.

## Changes and findings

- New [openalex_release.py](../../src/scientific_network/collect/openalex_release.py)
  and CLI command `release-acquire` (`--preflight-only`, `--limit` trial that writes
  nothing). `SourceError` now carries the HTTP status so a 404 is "not found".
- Preflight on 2026-11-08 03:22: budget $1/day, $1 remaining, list request $0.0001,
  singleton $0; 273 batches, worst case $0.1092 (4 attempts each).
- **Finding:** in a 100-paper trial, 10 papers had two OpenAlex works for one DOI: a
  crawled record whose landing page is the official AAAI page, and a Crossref record
  merged with the arXiv preprint (different type, reference count and often
  author IDs). Treated as a failure reason (the 30-minute box began 03:24). Rule
  implemented: among duplicates that pass the title and author-count checks, take the
  single record whose landing page equals the roster official URL, keep the others as
  alternates and flag whether their author IDs agree; otherwise leave in review.
- The OpenAlex `select` gained `type` and `primary_location` (release-v1.yaml).

## Result (CP1)

Run 2026-11-08 03:23–03:31 +07:00 (7 min 14 s), config
[release-v1.yaml](../../configs/release-v1.yaml), roster v10 sha256 `84ff8ca7…`:

| Measure | Value |
| --- | --- |
| Papers derived and requested | 13,617 (DOI derived for every row, no duplicate DOI) |
| Matched | **13,606 (99.92%)**, of which 2 accepted with a title-similarity flag |
| Review | 11: 9 duplicate-DOI works not resolvable, 2 author-count mismatches |
| Not found | 0 (7 singleton retries, all recovered) |
| Duplicate-DOI works | 264 resolved by the official landing page; 66 of those have differing author IDs between the two records; 9 left in review |
| Abstracts | 13,606 of 13,606 matched works |
| Requests | 337 batch + 7 singleton, all network; $0.0337 of the $1 daily allowance used |
| Worst match rate by venue-year | AAAI 2021, 99.64% (6 of 1,654 in review); AAAI 2024 and IJCAI 2022–2025 are 100% |
| Publication year differs from roster | 1 paper |

The 95% bar was met, so no extra time was spent on the failure reason. The 11
review papers keep PUBLISHED_IN and get an `unresolved_author_reason` in Phase 3.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run pytest -q -p no:cacheprovider tests/test_release_acquisition.py` | passed; 45 passed (DOI derivation incl. malformed rows, match rule, duplicate-DOI rule, scope checks, orchestration with a fake cache and mock transport) | offline |
| `research-network release-acquire --config configs/release-v1.yaml --preflight-only` | passed, exit 0; 273 batches, worst case $0.1092 | `reports/runs/WORK-2026-11-08-027/preflight.json` |
| `research-network release-acquire --config configs/release-v1.yaml --limit 100` (trial) | exit 0; found the duplicate-DOI pattern; nothing written | `reports/runs/WORK-2026-11-08-027/trial.json` |
| `research-network release-acquire --config configs/release-v1.yaml` | passed, exit 0 | [acquisition.json](../../reports/release-v1/acquisition.json); `works.jsonl` 129 MB (ignored) sha256 in the report |
| API key absent from `acquisition.json`, `works.jsonl` and cache request metadata | passed (0 hits) | inline script |
| Full suite | passed; 343 passed, 1 skipped | includes Phase 3 builder tests |

## Decisions

[D040 amendments](../decisions.md#d040-amendments): duplicate-DOI rule and the extra
`select` fields.

## Open issues and limitations

- 66 accepted papers rest on an OpenAlex record whose author IDs differ from its
  duplicate's. They are flagged in `match.duplicate_author_ids_agree`; the edge audit is
  the measure of any error this causes. Phase 3 still checks each position's name.
- OpenAlex content is a snapshot of 2026-11-08; the cached raw responses make the run
  reproducible but a fresh fetch may differ.
- The `rate-limit` response echoes a masked key; only numeric fields are stored.
- Phase 3 builder (`resolve/release.py`, `release-graph`, 24 tests) is written but not yet
  run on `works.jsonl`.

## Next step

Phase 3: run `research-network release-graph --config configs/release-v1.yaml`, measure
memory and time, check name-mismatch rate (fallback at 5%), and write
`reports/release-v1/graph-summary.json`. Acceptance: validation passes and all ten
relations are nonempty.

## Corrections

None.
