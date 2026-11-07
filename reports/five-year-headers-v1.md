# Five-year development PDF headers and source review

Measured **6 November 2026 (+07:00)** under D022–D024. This is a bounded diagnostic
stage on the previously frozen development sample. It does not establish complete
conference coverage, accepted people/affiliations or independent scientific accuracy.

- **68 selected development papers; 66 parsed headers.**
- **68 PDF sources available locally**, 283,508,927 bytes.
- **47 papers** have parsed affiliation blocks.
- **62 titles** and **48 complete ordered bylines** agree with the official roster.
- **45 papers** pass the title/detail/roster/unique-name binding checks.
- **255 deduplicated author–paper–institution candidates**; **56** have an exact printed-name match in that author's complete provider authorship.
- **1 previously withheld metadata record remains withheld**. Inspecting its PDF never overrides its status or accepts an author alias.
- **Zero held-out papers accessed, zero accepted identities/triples, zero graph imports.**
- External consolidation is disabled. No new OpenAlex requests, full-corpus PDFs,
  fulltext/reference pipeline or model downloads occur in this stage.

These are automated development source checks. GROBID can misread author markers,
combine affiliations, omit authors or extract the wrong title. Candidate counts are
not factual edges. Exact metadata agreement alone is insufficient for identity or
printed-marker acceptance; public ORCID publication corroboration, canonical-work
review and source-specific checks remain necessary. Independent precision, recall
and F1 are unmeasured. All release thresholds remain unchanged.

## Conference-year diagnostics

New diagnostics cover 2021/2022/2024/2025. The 2023 sample's 240 PDFs are separate
historical evidence, not part of this denominator.

| Year | Selected | Parsed | Parse review |
| --- | ---: | ---: | ---: |
| 2021 | 16 | 16 | 0 |
| 2022 | 18 | 18 | 0 |
| 2024 | 18 | 18 | 0 |
| 2025 | 16 | 14 | 2 |

## Source-series diagnostics

These are the selected sample's counts, not whole-venue coverage or error estimates.

| Series | Selected | Parsed | Candidate-binding papers | Affiliation candidates |
| --- | ---: | ---: | ---: | ---: |
| venue:acl | 4 | 4 | 3 | 16 |
| venue:aistats | 1 | 1 | 1 | 3 |
| venue:coling | 2 | 2 | 2 | 5 |
| venue:colt | 1 | 1 | 0 | 3 |
| venue:cvpr | 7 | 7 | 5 | 28 |
| venue:eccv | 4 | 4 | 3 | 13 |
| venue:emnlp | 2 | 2 | 1 | 7 |
| venue:iccv | 1 | 1 | 0 | 0 |
| venue:icml | 6 | 6 | 4 | 18 |
| venue:ijcai | 8 | 8 | 7 | 39 |
| venue:kr | 8 | 8 | 8 | 30 |
| venue:mlsys | 8 | 8 | 4 | 3 |
| venue:neurips | 8 | 8 | 5 | 66 |
| venue:rss | 8 | 6 | 2 | 24 |

## Evidence and reproduction

- [Workflow and exact command](../docs/five-year-collection.md#selective-frozen-development-pdf-headers-d024).
- [Measured aggregate JSON](five-year-headers-v1.metrics.json).
- [Extraction configuration](../configs/five-year-headers-v1.yaml).
- [Work log](../docs/work-log/2026-11-06-004-five-year-headers.md).
- Immutable local outputs: `data/interim/five-year-headers-v1/{papers,source-review,summary}.json`.
- Frozen sampling config, every old/new test ID and historical graph remain intact.
- PDFs, TEI, full abstracts, author/institution candidate rows and raw console logs
  remain local/ignored; unknown source rights do not authorize redistribution.
- Public Site keeps its native historical 399-node/533-edge explorer; base Neo4j
  was 154/211 at the preflight read-only check. Post-run services became unavailable
  when the Docker daemon stopped responding; no database writes were performed. The 402/538 candidate stays separate.

input metadata SHA-256: `af4fb53e0623ccaca9a668fdbd68d8e2e162de779fa3161f59761cb6b0c0d8f2`

manifest SHA-256: `4de5facc7c7e11ce5f66cc3788f1bf045e2dd1e3ab1799a646c3046d84597a3d`

membership SHA-256: `fdaa5e742c7c2e4a96c2d1d70df48103f758ec82fbbe01f8005adb4598aa674f`

selected diagnostics SHA-256: `cf68ac15e42861a17cccc7a8a7259e046e9a81e2c2a160e6dea7e25466042fe0`

extraction config SHA-256: `a60de76dafbde0792504c24a65f0b383e9b7a8d3cd2f1e0760b83b6bf5e86548`

extracted papers SHA-256: `ce769d553056e1e8c2ed43d49b513645ee4e364bc4de116092247b7d91cc832c`

source review SHA-256: `ded334896c4de3058f93418b16c0cf91463b99f92a497273bd52bb1d008d1b28`

Next: resolve canonical works and public-ORCID publication evidence, inspect
printed author–affiliation markers, retain contradictory/unverifiable cases in
review, and materialize only accepted support into a versioned isolated graph.
Do not infer accuracy or release readiness from parsing success.

## Development source inspections and checks

Five printed first pages were inspected as development evidence, not an independent
accuracy sample. The MLSys 2025 PDF corroborates its roster's full ordered byline
and five numbered author–institution mappings; its citation export abbreviates a
given name. The original metadata record remains withheld, with no identity alias
or acceptance override. GROBID omitted two institution entities and preserved a
broken line-wrap institution string on that paper.

The COLT 2022 PDF labels its proceedings editors separately; GROBID included those
editors as authors and omitted the second actual author. All positional bindings
for that paper remain unresolved. One IJCAI shared printed block corroborates two
candidate positions, without accepting either researcher identity.

RSS 2025 p046 and p108 have visible rendered titles/bylines, but `pdftotext` extracts
no first-page text. Both GROBID attempts returned HTTP 500. Their parse-review
records are retained; an OCR or alternate-source method is required. No unbounded
retries or OCR/model installation was performed.

**130 offline tests passed**. Extraction/replay both exit 1 for the two preserved
parse-review records, and their summaries are identical. All **7,297** protected
input/artifact files remain unchanged; **269** distinct evidence objects were
hash-verified. There were **zero new OpenAlex requests** and zero held-out overlap.
Before collection, Neo4j and GROBID were healthy. After collection Docker became
unreachable, preventing a fresh database reconciliation; no DB writes were issued.
See the [small source-note ledger](../data/manifests/five-year-printed-review-v1.json).
