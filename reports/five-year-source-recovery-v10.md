# Official source recovery v10 — MICCAI 2024

**Recorded:** 7 November 2026, Asia/Bangkok (UTC+07:00)  
**Method:** `five-year-official-rosters-v10`  
**Configuration:** [`corpus-five-year-v10.yaml`](../configs/corpus-five-year-v10.yaml)  
**Correction evidence:** [`five-year-source-corrections-v8.json`](../data/manifests/five-year-source-corrections-v8.json)  
**Decision:** [D033](../docs/decisions.md#d033--miccai-2024-full-proceedings-reconciliation-2026-11-07)

V10 overlays the immutable v9 roster. The official MICCAI Society accepted-paper
page lists **856** numbered 2024 research records. Springer’s official main
proceedings comprise **12 volumes** and **857 unique chapter records**, inspected
across **49 table-of-contents pages**. The captured Springer book description and
series index separately report 857 full papers / chapters. The series index count
is retained as a catalog counter and is not used alone as acceptance evidence.

All 856 Society records reconcile one-to-one with distinct Springer chapters:
**836 exact-title matches** and **20 unique title-and-byline matches**. The one
publisher-only chapter is a correction notice tied to a Society-listed paper; it
is nonresearch material and is excluded. No accepted Society record remains
unresolved. Under the existing D015 policy, the full 856-record Society roster is
eligible as the main archival research-paper set. No track or scope policy changed.

| Springer eISBN | Captured contents pages | Unique chapter records |
| --- | ---: | ---: |
| 978-3-031-72069-7 | 4 | 71 |
| 978-3-031-72083-3 | 4 | 73 |
| 978-3-031-72086-4 | 4 | 71 |
| 978-3-031-72089-5 | 4 | 70 |
| 978-3-031-72104-5 | 4 | 75 |
| 978-3-031-72111-3 | 4 | 69 |
| 978-3-031-72114-4 | 4 | 69 |
| 978-3-031-72117-5 | 4 | 70 |
| 978-3-031-72120-5 | 4 | 73 |
| 978-3-031-72378-0 | 5 | 72 |
| 978-3-031-72384-1 | 4 | 72 |
| 978-3-031-72390-2 | 4 | 72 |
| **Total** | **49** | **857** |

Official source routes: the [MICCAI 2024 Society list](https://papers.miccai.org/miccai-2024/),
[Springer MICCAI series index](https://link.springer.com/conference/miccai), and the
[Springer 12-volume main-proceedings set](https://link.springer.com/book/10.1007/978-3-031-72378-0).
The correction manifest binds the official source URLs, response hashes, retrieval
metadata, and per-volume page/chapter totals. The captured pages and full roster
remain ignored local data; only aggregate counts and links are published here.
No paper PDFs were downloaded.

## Measured v10 roster

| Measure | V10 |
| --- | ---: |
| Candidate editions | 170 |
| Eligible / verified no-edition | 98 / 10 |
| Unresolved roster/adapter / access-unavailable | 22 / 40 |
| Roster observations | 94,857 |
| Included / excluded / record review | 91,355 / 3,502 / 0 |
| MICCAI 2024 included / correction excluded | 856 / 1 |
| Guarded assignments / test assignments | 76,629 / 1,095 |

The 2024 overlay adds 857 roster observations to v9: 856 included Society records
and one excluded correction. All **36 inherited v9 edition roster/summary
artifacts** retain their recorded hashes. The fresh isolated v10 replay reproduced
all **42 output-file hashes** in the saved v10 summary.

Discovery returned **exit 1 as expected** because 62 candidate editions remain
incomplete. MICCAI 2022 remains unresolved (official accepted-list route HTTP 522;
Springer full-paper/index counts 574/576). AAMAS 2023 remains unresolved; the
other 20 unresolved rows are adapter gaps, and 40 publisher-access candidates
remain. P01 is partial. All 76,629 frozen assignments, including 1,095 tests,
remain guarded; v10 created no split. No metadata/PDF enrichment, canonical merge,
graph write, or database operation occurred. P02 remains no-go for broader
enrichment, and the diagnostic/pregraph inputs remain bound to v2.

The discovery manifest SHA-256 is
`84ff8ca78073e5d5e0d94f909aac63d18d71435cbd60f30630b7c3090b3c1cbe`; the edition-ledger SHA-256 is
`720de4a55665cd35f58ad1e59edf892425167099934a232c31d3db6b260bfd79`. The configuration hash is
`3af300dd109e846726da0c8b7aaae73ab0f6e9ee968019441ee39c12293ff562`; the source-correction manifest hash is
`aa66cad3a9ebc2de5a838644e245e3707378ad7f660f118781ab7a8bdb544ee5`. The full output hash map and aggregate metrics are in
[`five-year-source-recovery-v10.metrics.json`](five-year-source-recovery-v10.metrics.json).
The public report does not expose per-record roster metadata. Structural
source/count reconciliation is not independent semantic accuracy, person
resolution, canonical work coverage, graph quality, or release readiness.

See the [170-row v10 ledger](five-year-edition-ledger-v10.csv),
[current source triage](../docs/five-year-source-triage.md),
[current status](../docs/status.md), and [WORK-006](../docs/work-log/2026-11-07-006-miccai-2024-source-closure.md).
