# Official source recovery v9 — MICCAI 2021–2025

**Recorded:** 7 November 2026, Asia/Bangkok (UTC+07:00)  
**Method:** `five-year-official-rosters-v9`  
**Configuration:** [`corpus-five-year-v9.yaml`](../configs/corpus-five-year-v9.yaml)  
**Correction evidence:** [`five-year-source-corrections-v7.json`](../data/manifests/five-year-source-corrections-v7.json)  
**Decision:** [D032](../docs/decisions.md#d032--miccai-roster-closure-and-unresolved-edition-counts-2026-11-07)

V9 adds three MICCAI year rosters to the immutable v8 baseline. The captured official
Society and conference accepted lists match Springer's full-paper counts for 2021,
2023 and 2025. MICCAI 2022 and 2024 remain unresolved because complete list evidence
does not reconcile. The v2-bound diagnostic/pregraph inputs, all earlier roster
versions and their frozen assignments are preserved. This run made no enrichment
requests, new split, canonical work merge, PDF download, graph write or database
operation.

## Measured roster

| Measure | v9 result |
| --- | ---: |
| Eligible editions | 97 |
| Verified no-edition findings | 10 |
| Unresolved roster/adapter editions | 23 |
| Publisher-access-unavailable editions | 40 |
| Incomplete edition candidates | 63 |
| Roster observations | 94,000 |
| Included | 90,499 |
| Excluded | 3,501 |
| Record-level review | 0 |
| Guarded frozen assignments | 76,629 |
| Protected test assignments | 1,095 |

| MICCAI year | Official captured roster | Springer full-paper count | Springer index counter | Disposition |
| --- | ---: | ---: | ---: | --- |
| 2021 | 531 | 531 | 535 | Eligible |
| 2022 | Not captured (HTTP 522) | 574 | 576 | Unresolved |
| 2023 | 730 | 730 | 732 | Eligible |
| 2024 | 856 | 857 | 857 | Unresolved |
| 2025 | 1,027 | 1,027 | 1,029 | Eligible |

The Springer index values are catalog counters, retained separately from year-specific
full-paper counts. The observed differences are not treated as additional accepted
research papers. 2022's accepted-paper route returned HTTP 522. The 2024 captured
Society list has one fewer numbered record than the Springer full-paper count. Both
years remain outside the eligible roster until their discrepancies are reconciled.

Official roster routes: [MICCAI 2021 accepted list](https://miccai2021.org/openaccess/paperlinks/),
[MICCAI 2022 accepted list](https://conferences.miccai.org/2022/papers/),
[MICCAI 2023 accepted list](https://conferences.miccai.org/2023/papers/),
[MICCAI 2024 Society list](https://papers.miccai.org/miccai-2024/), and
[MICCAI 2025 Society list](https://papers.miccai.org/miccai-2025/). Springer year-book
descriptions are [2021](https://link.springer.com/book/10.1007/978-3-030-87193-2),
[2022](https://link.springer.com/book/10.1007/978-3-031-16431-6),
[2023](https://link.springer.com/book/10.1007/978-3-031-43907-0),
[2024](https://link.springer.com/book/10.1007/978-3-031-72378-0), and
[2025](https://link.springer.com/book/10.1007/978-3-032-04927-8); the aggregate
catalog counters are on the [Springer MICCAI index](https://link.springer.com/conference/miccai).
Raw response hashes are in the correction manifest.

The 2021 and 2023 lists provide titles/record IDs without author bylines; 2025's
Society listing includes BibTeX names. These are roster observations, not resolved
people or accepted graph claims. Under D015, authoritative detail bylines remain
required before work matching or core-paper acceptance. No per-record roster is
published.

## Verification and limits

The offline discovery command returned **exit 1 as expected** because 63 edition
candidates remain incomplete. It produced 94,000 roster observations, of which
90,499 are in eligible editions. The v9 manifest SHA-256 is
`381b0eade87bc8272b17e184eb27d2e5c773a41641eceb6a38ae6f964bff2b4b`; the edition-ledger SHA-256 is `b8139167f946aa7ae06a75bd4a4f23ff84fbef68ac3253685688295e2c9a6846`. All
`30` inherited v8 edition artifacts have the same recorded SHA-256 values.
The v9 output guards all 76,629 frozen assignments, including 1,095 test assignments;
no new split was created.

The parser validates complete contiguous numbered rosters and source hashes. The
full offline suite passed **198 tests**, including five focused MICCAI parser
tests. The captured HTML and complete per-record rosters are ignored local inputs;
the correction manifest records their hashes but does not make a clean checkout
self-contained for replay. Structural/source-contract checks do not measure
independent semantic accuracy, person resolution, canonical works, release coverage
or graph quality. P01 remains incomplete. P02 remains **no-go for
broader enrichment** while the canonical population, prospective P03 design, live
resource/storage limits and reviewer capacity remain unmeasured.

See the [170-row v9 ledger](five-year-edition-ledger-v9.csv),
[aggregate metrics](five-year-source-recovery-v9.metrics.json),
[current source triage](../docs/five-year-source-triage.md), and
[current status](../docs/status.md).
