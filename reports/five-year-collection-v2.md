# Five-year collection and frozen diagnostics — revision 2

Measured **6 November 2026 (+07:00)** under D022/D023. Scope remains **34 series,
2021–2025**, with all **170 venue–year candidates** retained. The first-pass v1
report, raw inputs, memberships, graphs and publication snapshots remain preserved.
This is development collection evidence; independent semantic accuracy is unmeasured.

## Corrected official rosters

- **78,321** official roster records: **75,655 included**, **2,666 excluded**.
- **79 eligible editions**, up from 67; **51 unresolved / 40 unavailable** remain.
  All included records are within eligible editions in this pass; no unknown-track
  records remain in collected editions. This does not prove full registry coverage.
- Counts are not deduplicated canonical works, resolved researchers or graph edges.
- NeurIPS 2025 position papers excluded; ECVA edition accordion/path checked;
  RSS year tied to official catalog dates plus edition numerals; KR Full/Short/Main
  headings mapped and named special/application tracks excluded. No gate relaxed.
- Source/catalog access does not itself establish redistribution rights. Unknown
  licenses and inaccessible/unsupported sources remain explicit; full rosters stay local.

| Conference year | Roster records | Included | Eligible editions | Other candidates |
| --- | ---: | ---: | ---: | ---: |
| 2021 | 11063 | 10917 | 16 | 18 |
| 2022 | 12520 | 12151 | 16 | 18 |
| 2023 | 14480 | 13935 | 15 | 19 |
| 2024 | 17698 | 16937 | 16 | 18 |
| 2025 | 22560 | 21715 | 16 | 18 |

## Prospective sample and leakage protection

All **14,909** historical assignments remain exactly unchanged, including the
**5,046** original assignments. Preliminary triage: 13,935 collected records retain
old assignments; 61,719 new eligible records await design, and one version candidate
is quarantined. Title links are conservative leakage guards; they never merge works.
Alternate-title versions without shared identifiers remain a detection limitation.

Before enrichment, froze **68 development diagnostics** and **170 new test groups**
across **34 source-family/year strata**. Each stratum has five reserved tests and
two development diagnostics, with explicit population/selection probabilities and
seed 20261106. **Zero held-out acquisition overlap**. Future versions must also
preserve these new reserved IDs; no silent sample redraws.

This diagnoses source layouts and new years, not all venues equally or independent
release accuracy. New diagnostics cover 2021/2022/2024/2025; the existing 2023
sample remains separate historical evidence. The later uniform 600-edge audit,
component annotation, recall/coverage and scientific evaluation have not run.

## Bounded metadata tranche

- **67 / 68** selected development papers acquired; **67 abstracts**.
- **36** strict OpenAlex work matches; none constitutes accepted researcher identity.
- **One withheld paper**: MLSys 2025 roster expands a given name while citation
  metadata abbreviates it. No forced alias/identity merge or threshold change.
- **Zero PDFs downloaded, zero new graph imports, zero held-out papers acquired.**
- OpenAlex used **$0.067 of the daily free allowance**; **$0.933 remained** at the
  post-run check. Prepaid balance/remnant were zero. Metadata failures and full
  abstracts remain ignored locally. Quota was checked before enrichment.
- **120 offline tests passed**. Structural/software checks are not semantic accuracy.

## Services and existing graph

Base Neo4j is healthy and remains **154 nodes / 211 edges** at read-only checks.
The existing GROBID service was started and `isalive` returns true; it was not used
for extraction in this metadata-only batch. The historical native Site explorer
remains **399 / 533**, and the reviewed **402 / 538** candidate remains separate.
No five-year graph, researcher count, precision, recall or F1 claim exists yet.

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
| ECCV | 4032 | unresolved: 3; verified_eligible: 2 |
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
| KR | 389 | verified_eligible: 5 |
| MICCAI | 0 | unresolved: 5 |
| MLSys | 247 | verified_eligible: 5 |
| NAACL | 2205 | verified_eligible: 4; unresolved: 1 |
| NeurIPS | 19024 | verified_eligible: 5 |
| RecSys | 0 | access_unavailable: 5 |
| Robotics: Science and Systems (RSS) | 575 | verified_eligible: 5 |
| SDM | 0 | access_unavailable: 5 |
| SIGIR | 0 | access_unavailable: 5 |
| UAI | 1109 | verified_eligible: 5 |
| WSDM | 0 | access_unavailable: 5 |
| The Web Conference (WWW) | 0 | access_unavailable: 5 |

## Reproduction and provenance

- [Workflow and exact stage commands](../docs/five-year-collection.md).
- [Machine-readable measured summary](five-year-collection-v2.json).
- [All 170 edition statuses/source hashes](five-year-edition-ledger-v2.csv).
- [Frozen diagnostic design](../configs/five-year-diagnostics-v1.yaml).
- Local immutable inputs: `five-year-roster-v2`, `five-year-reconciliation-v2`,
  `five-year-splits-v1`, `data/interim/five-year-acquired-v1`.
- [Work entry/checks](../docs/work-log/2026-11-06-003-five-year-diagnostics.md).

roster SHA-256: `4de5facc7c7e11ce5f66cc3788f1bf045e2dd1e3ab1799a646c3046d84597a3d`

edition ledger SHA-256: `4817c2cd2fbd9027759149165d636b16e9b4df16a5b36eaddeb94e4e7dd504f1`

frozen membership SHA-256: `fdaa5e742c7c2e4a96c2d1d70df48103f758ec82fbbe01f8005adb4598aa674f`

selected diagnostics SHA-256: `cf68ac15e42861a17cccc7a8a7259e046e9a81e2c2a160e6dea7e25466042fe0`

metadata papers SHA-256: `af4fb53e0623ccaca9a668fdbd68d8e2e162de779fa3161f59761cb6b0c0d8f2`

Next: selective PDF/header extraction and source-specific author/affiliation review
on the frozen development records, including the withheld byline. Keep ORCID/PID
corroboration, exact author–paper–organization mappings, provider-version quarantine,
held-out isolation and independent review before any new isolated graph import.
Do not scale full enrichment solely because roster counts exceed numerical targets.
