# Official source recovery v8 — AAMAS 2021–2025

**Recorded:** 7 November 2026, Asia/Bangkok (UTC+07:00)  
**Method:** `five-year-official-rosters-v8`  
**Configuration:** [`corpus-five-year-v8.yaml`](../configs/corpus-five-year-v8.yaml)  
**Correction evidence:** [`five-year-source-corrections-v6.json`](../data/manifests/five-year-source-corrections-v6.json)  
**Decision:** [D031](../docs/decisions.md#d031--aamas-official-roster-closure-and-2023-reconciliation-hold-2026-11-07)

Roster v8 overlays four complete official AAMAS rosters onto v7. It preserves all
170 edition candidates and every prior roster/config version. The v2-bound
diagnostic and pregraph inputs are unchanged. This run performs no enrichment,
sample allocation, canonical work merge, PDF download or graph/database write.

## Measured roster

| Measure | v8 result |
| --- | ---: |
| Eligible editions | 94 |
| Verified no-edition findings | 10 |
| Unresolved roster/adapter editions | 26 |
| Publisher-access-unavailable editions | 40 |
| Incomplete edition candidates | 66 |
| Roster observations | 91,712 |
| Included | 88,211 |
| Excluded | 3,501 |
| Record-level review | 0 |
| Guarded frozen assignments | 76,629 |
| Protected test assignments | 1,095 |

| AAMAS year | Official research section | TOC records | Included | Excluded | Disposition |
| --- | --- | ---: | ---: | ---: | --- |
| 2021 | Main Track | 304 | 151 | 153 | Eligible |
| 2022 | Main Track | 306 | 166 | 140 | Eligible |
| 2023 | Main Track: Full Papers requires reconciliation | 528 | 0 | 0 | Unresolved |
| 2024 | Full Research Papers | 460 | 230 | 230 | Eligible |
| 2025 | Research Paper Track | 479 | 260 | 219 | Eligible |

The 2021–2025 records are parsed from the [official IFAAMAS proceedings pages](https://www.ifaamas.org/proceedings.html):
[2021](https://www.ifaamas.org/Proceedings/aamas2021/forms/contents.htm),
[2022](https://www.ifaamas.org/Proceedings/aamas2022/forms/contents.htm),
[2023](https://www.ifaamas.org/Proceedings/aamas2023/forms/contents.htm),
[2024](https://www.ifaamas.org/Proceedings/aamas2024/forms/contents.htm), and
[2025](https://www.ifaamas.org/Proceedings/aamas2025/forms/contents.htm). The
included category names are taken literally from each official contents page;
all other enumerated categories are excluded under D015's existing AAMAS policy.
The four eligible rosters contain complete bylines and unique official PDF record
IDs. PDFs were not downloaded.

## AAMAS 2023 remains unresolved

The [official news page](https://www.ifaamas.org/AAMAS/aamas2023/news.html)
announces 237 full papers and 221 extended abstracts. The [accepted-paper page](https://www.ifaamas.org/AAMAS/aamas2023/accepted_papers.html)
lists 237 full-paper titles but 219 extended-abstract titles. A bounded exact-title
join between the accepted list and official proceedings contents matches 225/237
full-paper titles; 12 title variants do not join exactly, and 35 of the exact-title
matches have differing author strings. These are automated reconciliation results,
not human adjudications. Because publication IDs and bylines are not completely
reconciled, v8 leaves the 2023 edition unresolved and adds no 2023 AAMAS roster
records.

## Rights, reproduction and limits

The official proceedings notices allow limited personal/classroom copying with
attribution and require permission or a fee for republication or redistribution.
Detailed captured pages and full rosters remain in the ignored local cache/output;
the tracked correction manifest contains source URLs, response hashes and
aggregate dispositions only. No per-record roster or PDF is published.

Reproduce the immutable overlay from its local hash-verified inputs:

```bash
uv run research-network discover \
  --config configs/corpus-five-year-v8.yaml \
  --output data/manifests/five-year-roster-v8 \
  --cache data/raw/five-year-source-cache-v8
```

The command returned **exit 1 as designed** because 66 edition candidates remain
incomplete. It produced 91,712 observations (88,211 included, 3,501 excluded),
94 eligible editions, 26 unresolved roster/adapter editions, and 40
access-unavailable editions. The v8
manifest SHA-256 is
`7906b44786c2251cfe87d26347c93913efbf2c60c6d75f0e400ad15faebd55a2`; the ledger
SHA-256 is
`bbcff1ff7575633ec6b78439a20974d0db7c4ba2225466577ce251e68d8b3f6e`. The full
offline suite passed: **193 tests**. The source overlay retains all 76,629
assignments, including 1,095 tests; it creates zero new splits and records zero
enrichment requests, PDF downloads or graph writes.

P01 remains incomplete. P02 remains **no-go for broader enrichment** while the
canonical population, prospective P03 frame, live resource/storage limits and
reviewer capacity remain unmeasured. The full five-year release and independent
accuracy, recall and coverage are not established by roster size or parser tests.
See the [170-row v8 ledger](five-year-edition-ledger-v8.csv),
[aggregate metrics](five-year-source-recovery-v8.metrics.json),
[source triage](../docs/five-year-source-triage.md), and
[current status](../docs/status.md).
