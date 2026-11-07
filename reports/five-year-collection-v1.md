# Five-year official roster collection — v1

Measured **6 November 2026 (+07:00)** under D022; partial first collection pass.
Scope: **34 series, 2021–2025**, all **170 venue–year candidates** retained.
Automated roster checks are not independent scientific review or semantic accuracy.

- **73,714** official roster records; **70,973** marked included, **2,556** excluded,
  **185** review records. Counts can contain alternate versions and are not unique works.
- **65,523** included records belong to **67** completely parsed eligible editions.
  Included records from incomplete editions cannot enter acquisition.
- Other candidates: **51 unresolved**, **40 access unavailable**, **12 need review**.
  No missing edition was inferred from an absent link or HTTP failure.
- **No five-year graph, resolved-person count or accuracy result.** Historical graphs
  and databases were not changed. No OpenAlex requests, PDFs or enrichment in this pass.

## Coverage by conference year

| Year | Roster records | Included records | Included in eligible editions | Eligible editions | Other candidates |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2021 | 10971 | 10750 | 10750 | 14 | 20 |
| 2022 | 10801 | 10432 | 10389 | 13 | 21 |
| 2023 | 14368 | 13823 | 13823 | 14 | 20 |
| 2024 | 15177 | 14416 | 14350 | 13 | 21 |
| 2025 | 22397 | 21552 | 16211 | 13 | 21 |

## Leakage triage

The offline triage preserved all **14,909** frozen expanded assignments (including
all **5,046** original assignments), with **13,823** matching collected records.
**57,149** included records await prospective design; **one** new version candidate
is quarantined. All other historical assignments remain unchanged even when their
edition is absent from this pass. No new splits or canonical work merges were made.

Exact normalized titles are conservative leakage guards, not identity evidence.
Alternate-title versions without shared identifiers remain a detection limitation.
The triage includes provisional records from incomplete editions, and does not
make them eligible. Complete edition checks, identifier/version review and frozen
sampling probabilities are still required before enrichment.

## Source/layout gaps

NeurIPS 2025 has 5,286 main-track records, 497 excluded Datasets and Benchmarks
records and 40 unknown position-track records; the entire edition remains in
review. ECVA 2022/2024 heading layouts, RSS year evidence, and KR track boundaries
need adapter review. Publisher access failures and unsupported main-track adapters
remain explicit; no access controls were bypassed. Missing catalog links do not
prove that an edition did not occur.

Raw responses and full rosters remain ignored locally. Terms/redistribution rights
are unknown unless supplied by the source; only permitted aggregate evidence and
rebuild instructions are tracked. Per-edition checks are automated contract checks,
not a human review of complete source terms or every scientific record.

## Edition status by series

| Series | Roster records | Edition statuses |
| --- | ---: | --- |
| AAAI | 0 | unresolved: 5 |
| AAMAS | 0 | unresolved: 5 |
| ACL | 5134 | verified_eligible: 5 |
| ACM Multimedia | 0 | access_unavailable: 5 |
| AISTATS | 2573 | verified_eligible: 5 |
| CIKM | 0 | access_unavailable: 5 |
| COLING | 1391 | unresolved: 3; verified_eligible: 2 |
| COLT | 826 | verified_eligible: 5 |
| Conference on Robot Learning (CoRL) | 1089 | verified_eligible: 5 |
| CVPR | 11674 | verified_eligible: 5 |
| EACL | 833 | verified_eligible: 3; unresolved: 2 |
| ECCV | 0 | unresolved: 3; needs_review: 2 |
| EMNLP | 5804 | verified_eligible: 5 |
| ICAPS | 0 | unresolved: 5 |
| ICCV | 6469 | verified_eligible: 3; unresolved: 2 |
| ICDM | 0 | unresolved: 5 |
| ICLR | 0 | unresolved: 5 |
| ICML | 10184 | verified_eligible: 5 |
| ICRA | 0 | unresolved: 5 |
| IJCAI | 4763 | verified_eligible: 5 |
| IROS | 0 | unresolved: 5 |
| KDD | 0 | access_unavailable: 5 |
| KR | 389 | needs_review: 4; verified_eligible: 1 |
| MICCAI | 0 | unresolved: 5 |
| MLSys | 247 | verified_eligible: 5 |
| NAACL | 2205 | verified_eligible: 4; unresolved: 1 |
| NeurIPS | 19024 | verified_eligible: 4; needs_review: 1 |
| RecSys | 0 | access_unavailable: 5 |
| Robotics: Science and Systems (RSS) | 0 | needs_review: 5 |
| SDM | 0 | access_unavailable: 5 |
| SIGIR | 0 | access_unavailable: 5 |
| UAI | 1109 | verified_eligible: 5 |
| WSDM | 0 | access_unavailable: 5 |
| The Web Conference (WWW) | 0 | access_unavailable: 5 |

## Reproduction and provenance

- Executable config: [`corpus-five-year-v1.yaml`](../configs/corpus-five-year-v1.yaml).
- [Commands and stage boundaries](../docs/five-year-collection.md).
- [Machine-readable measured summary](five-year-collection-v1.json).
- [All 170 edition statuses and source hashes](five-year-edition-ledger-v1.csv).
- Local immutable roster/ledger: `data/manifests/five-year-roster-v1/`.
- Local leakage triage: `data/manifests/five-year-reconciliation-v1/`.
- [Work entry and exact checks](../docs/work-log/2026-11-06-002-five-year-collection.md).

config_sha256: `9914ea3ca428047078ebe106d784ab8852f2761637fe43e8a52cf85cd14ba402`

manifest_sha256: `7a039e31f6a83dc894d93a72e8160fb24603d71a1b02ca867f11e909e9a5dc68`

edition_ledger_sha256: `5d2accecb5c1bc9e05e6824fb628ba759447638e0a518a29e2cede6d6662f6de`

Next: correct/review edition/track gaps under **new versions**, reconcile work
identifiers and historical exposure, then freeze the prospective diagnostic design
before a bounded metadata/PDF tranche. Keep the 11 November deadline and unchanged
quality gates; roster size is not evidence that the release passes them.
