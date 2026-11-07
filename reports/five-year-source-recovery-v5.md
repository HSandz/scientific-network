# Official source recovery — 6 November 2026 (D027)

This bounded iteration recovers official AAAI/ICAPS rosters under the unchanged
2021–2025 / 34-series boundary. It makes no enrichment API requests and accepts no new identities,
affiliations or topics, and builds/imports no graph. The current roster is v5;
v3/v4 and all earlier diagnostics/pregraph bundles remain immutable.

| Measure | Current result |
| --- | ---: |
| Candidate editions retained | 170 |
| Eligible editions | 88 (was 79) |
| Roster records, including exclusions/review | 88,608 |
| Included records within eligible editions | 85,802 |
| Excluded / review records | 2,758 / 48 |
| Edition gaps: unresolved / unavailable / review | 41 / 40 / 1 |
| Prior roster rows preserved identically | 78,321 |
| Frozen assignments guarded / test assignments | 76,629 / 1,095 |
| New splits / canonical merges / graph writes | 0 / 0 / 0 |

All 925 historical expanded tests and 170 newly reserved test groups are guarded;
the original legacy assignments remain identical subsets. No held-out paper
enrichment occurs. Roster observations are not canonical works, researchers,
graph nodes, accepted factual edges or independent scientific accuracy.

## Recovered source evidence

| Conference year | AAAI main records | ICAPS main records | ICAPS status |
| --- | ---: | ---: | --- |
| 2021 | 1,654 | 49 | verified_eligible |
| 2022 | 1,319 | 50 | verified_eligible |
| 2023 | 1,578 | 56 | verified_eligible |
| 2024 | 2,331 | 82 | verified_eligible |
| 2025 | 3,028 | 0 | needs_review |

AAAI: six linked archive pages cover the target-year boundary, with 80 contiguous
main technical issues parsed. Eleven special/student/IAAI/EAAI issues are recorded
as excluded catalog routes and not fetched; their article counts remain unknown.
ICAPS: five official issue tables of contents were inspected. The 2021–2024
Main Track contributes 237 eligible records. In 2025, 48 theoretical/algorithmic/
modelling/tools records remain in review and four editorial/position records are
excluded; main-track membership cannot be inferred from research-category names.

Every recovered record retains the literal section, exact official article URL,
archive/issue evidence hashes and original retrieval date. Exact issue headings,
complete pagination, year order, unique IDs and issue sequences gate eligibility.
AAAI 2021 technical-focus headings and the 2024 ROB shorthand are exact,
edition-bound variants within verified main technical issues (D027).

## Version and leakage safeguards

- V3 safely recovered four ICAPS editions, but withheld AAAI on an irrelevant older
  archive title after the 2020 boundary: 83 eligible editions overall.
- V4 stops at the first corroborated pre-2021 issue; main-heading variants stayed
  in review: 86 eligible editions overall.
- V5 recognizes four literal edition-specific AAAI headings: 88 eligible editions.
  It ran with HTTP disabled using only the immutable sources already cached.
- All three completed versions replay identically with `SourceCache.get` disabled.
- The other 160 edition observations are inherited unchanged from v2; their dates
  are historical source observations, not newly verified availability.
- Across all included rows, 75,655 preserve existing assignments, 10,143 await a
  future prospective design, and four are quarantined as version candidates.
  Exact normalized titles guard leakage only; alternate-title versions remain a
  limitation and no work or person is merged.

## Checks and limits

- **177 offline tests passed**; 21 new synthetic OJS contract cases.
- **8,104 prior artifacts unchanged** before mutable report updates;
  **562 source descriptors/objects verified**.
- **92 new official HTML responses**, all from `ojs.aaai.org`; no OpenAlex/ORCID,
  paper PDF or model requests. No paid service or database operation.
- Discovery exits **1 intentionally** while 82 edition gaps/48 track-review records
  remain. Retained partial results are not a complete corpus or successful release.
- No new Neo4j/GROBID health or database-count check was performed: this collector
  does not use them. Last iteration’s service results are historical.
- Identity/affiliation/topic support stays at task 006’s frozen diagnostic results.
  The old pregraph freeze is still bound to v2 and remains false; it was not rerun
  or silently relabeled against this larger roster. Independent labels remain absent.

## Reproduction and next action

```bash
uv run research-network discover \
  --config configs/corpus-five-year-v5.yaml \
  --output data/manifests/five-year-roster-v5 \
  --cache data/raw/five-year-source-cache-v1
```

Requires the exact protected v2 baseline/frozen files recorded in the config.
Use new config/output versions for changed sources or methods. Full rosters,
raw HTML and detailed per-record leakage candidates remain ignored/local. The
[permitted summary](five-year-source-recovery-v5.metrics.json) and
[170-row edition ledger](five-year-edition-ledger-v5.csv) are tracked aggregates.

Next: corroborate ICAPS 2025’s track policy, address remaining accessible source
families, and freeze a budgeted supplemental development/test design before any
new enrichment. Obtain independent development labels for component calibration.
Do not build a graph from the old failed-readiness freeze.

Config SHA-256: `e3f585ae6d9499cf97ffa5b4cf539a9c6c27c1dd179e6bdb69c8f69816def1c7`.
Manifest SHA-256: `cf2a24dca0238820c9637e2a46a64cecd9ef84cb7cdc54b2acb85b805f64faca`.
Ledger SHA-256: `c5e42b666164967f9cf0ff56ef2cb2b27c1159757aa82d91152bc6bd1492c328`.
Method: `five-year-official-rosters-v5`; no new graph version.
