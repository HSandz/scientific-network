# Conference scope — 2021–2025 planning revision

The course's NeurIPS/ICML examples do not restrict venue selection (D014). The
current core target is **2021–2025** (D018), retaining the same 34 flagship series.
**Planning, documentation and Site updates only; no new pipeline implementation
or research collection.** D015 authorized historical 2023 staging. See
[the temporal plan](five-year-scope.md) for future prerequisites.

## Explicit flagship registry

This is a curated boundary, not a universal ranking, verified CORE A*/A
classification or every computer science conference. Include specialized flagships
as well as large general venues; do not select papers by fame, citations or labels.

| Area | Conference series | Series count |
| --- | --- | ---: |
| General AI, machine learning and systems | NeurIPS, ICML, ICLR, AAAI, IJCAI, MLSys | 6 |
| Vision, multimedia and medical imaging | CVPR, ICCV, ECCV, ACM Multimedia, MICCAI | 5 |
| Natural language processing | ACL, EMNLP, NAACL, EACL, COLING | 5 |
| Data mining, web, retrieval and recommendation | KDD, The Web Conference (WWW), SIGIR, WSDM, RecSys, CIKM, ICDM, SDM | 8 |
| Statistical learning, uncertainty and theory | AISTATS, UAI, COLT | 3 |
| Robotics and embodied learning | ICRA, IROS, Robotics: Science and Systems (RSS), Conference on Robot Learning (CoRL) | 4 |
| Agents, reasoning and planning | AAMAS, KR, ICAPS | 3 |

The planning matrix has **170 venue–year candidates** (34 × five years), not a
confirmed edition count. Verify official edition year, track, source rights and
lawful access per candidate. Annual/biennial cadence alone is not verification.
Retain no-edition/unavailable/unresolved states. ECCV/NAACL/COLING's no-2023-edition
records remain historical for that year, not exclusions from all five years.

## Inclusion and exclusion rules

- Target complete official main archival research-paper rosters per verified
  edition. Include full/short main research papers where distinguished; exclude
  poster-only abstracts, workshops, tutorials, invited/editorial/doctoral material,
  withdrawn/rejected papers and supplementary files counted as papers.
- ACL-family main long/short papers qualify. Findings, demos, workshops, student
  research and nonresearch industry tracks remain outside this release.
- Exclude NeurIPS Datasets and Benchmarks. KDD starts with Research Track;
  Applied Data Science and other tracks require a separate decision.
- Preserve conservative COLT Original Papers and AAMAS regular research policies
  from D015; verify edition-specific layouts and track changes before future use.
- Eligibility depends on source/edition/track evidence, not topic classification.
  Unknown tracks stay in review; a shared volume/event name is insufficient.
- Reconcile cross-year/cross-venue versions through identifiers/content/bylines,
  never title alone. Keep one primary Venue, crosswalks and reversible decisions.
  Ambiguous work identity remains review, not a guessed merge.
- Preserve five labels, ten predicates, author-specific affiliations and accepted
  core support. Core citations use verified in-window targets; external context
  cannot satisfy release-size requirements.

## Configurations and historical evidence

`configs/conference-scope-2021-2025.yaml` is the new **planning-only registry**,
with implementation/collection disabled and no executable `editions` list. Catalog
URLs are leads, not verified endpoints. Do not pass it to pipeline commands or
create split assignments during this task.

Keep `configs/conference-scope.yaml` (D014's 2023 planning registry),
`configs/corpus.yaml`, `configs/quality.yaml`, executable
`configs/corpus-extended-v2.yaml`, frozen inputs and Sites snapshots unchanged.
Historical 2023 work covered 17 of 31 planned in-year editions; 14 unresolved and
three no-edition cases remain in that ledger. Those counts do not describe the
five-year target. [Existing workflow](extended-workflow.md),
[measured evidence review](../reports/evidence-review-v1.md).

Preserve all legacy/expanded held-out IDs. Design supplemental venue–year sampling,
version leakage protection, annotation hours and population weights before a later
authorized run. Do not multiply old quotas or size targets by five. No new roster,
split, measurement or collection is created here. The [five-year plan](five-year-scope.md)
specifies annual/cumulative support, citation-age controls and resource estimates.
