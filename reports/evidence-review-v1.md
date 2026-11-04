# Diagnostic evidence review — 4 November 2026

Recovered all **250 selected metadata records** and parsed **240 PDFs** after
Docker became available. Three recovered papers enter a separate **402-node /
538-edge candidate graph**; two conflicting PDF bylines remain withheld. Both
loaded Neo4j databases and the existing HTML report retain their earlier snapshots.
This is development review by Codex, not an independent semantic audit.

| Measure | Previous snapshot | Candidate |
| --- | ---: | ---: |
| Acquired diagnostic metadata | 245 | 250 |
| Abstracts available in acquired metadata | 235 | 240 |
| Parsed PDFs | 235 | 240 |
| Strict OpenAlex work matches | 145 | 145 |
| Core papers | 245 | 248 |
| Resolved researchers | 85 | 85 |
| Organizations | 32 | 32 |
| Accepted author–paper–organization triples | 38 | 38 |
| All domain nodes | 399 | 402 |
| All edges | 533 | 538 |
| Factual R1–R4 edges | 369 | 372 |
| Inferred topic edges | 108 | 110 |
| Curated taxonomy / derived edges | 16 / 40 | 16 / 40 |
| Nonempty relationship types | 8 | 8 |

## Five byline decisions

| Official record | Finding | Core disposition |
| --- | --- | --- |
| [EACL 152](https://aclanthology.org/2023.eacl-main.152/) | Visible roster-consistent byline; citation export differs in accents/initials | Retain publication byline |
| [EACL 280](https://aclanthology.org/2023.eacl-main.280/) | Printed PDF changes author order; metadata also changes a name | Withhold pending version/byline adjudication |
| [EMNLP 401](https://aclanthology.org/2023.emnlp-main.401/) | Visible roster-consistent byline; citation export differs in spelling/initials | Retain publication byline |
| [EMNLP 536](https://aclanthology.org/2023.emnlp-main.536/) | Visible roster-consistent byline; citation export expands a given name | Retain publication byline |
| [MLSys record](https://proceedings.mlsys.org/paper_files/paper/2023/hash/8e3e27d07b3f663b7f85c819b9692163-Abstract-mlsys2023.html) | Unicode parsing repaired; PDF has nine authors, HTML eight | Withhold; no transliteration merge |

Full ordered work matching remains strict. None of the five recovered metadata
records obtains an exact OpenAlex match; the three admitted papers add publication
edges, not newly resolved researchers. Decisions, hashes and locators are in
[the input-bound ledger](../data/manifests/reviews/source-review-v2.json).

## Identity and affiliation evidence

The original **718 review rows** were preserved and triaged offline:

| Technical triage | Rows |
| --- | ---: |
| Public ORCID works empty / no target / uncached request failure | 133 / 244 / 3 |
| Identifier gaps | 187 |
| No exact work match / ambiguous candidates | 98 / 2 |
| Institution alias or hierarchy / missing author-specific evidence | 17 / 16 |
| Possible cross-author PDF mapping | 7 |
| PDF name segmentation / official PDF unavailable | 3 / 8 |

Stored technical checks passed for 85 accepted identity claims and 38 affiliation
triples; **813 distinct cached source objects** were hash-checked in baseline
triage. These are provenance/consistency checks, not precision estimates.

Visual first-page inspection of EACL 164 and 171 corroborated five printed
affiliations: Touileb→Bergen, Velldal→Oslo, Carrella→Bristol, Miani→Neuchâtel,
Lewandowsky→Bristol. GROBID had repeated combined institution lists under several
authors, generating extra review rows. The original author-specific provider
intersection had already accepted these five correct mappings. The new ledger
adds direct printed-source evidence; **zero affiliation triple IDs were added or
removed**. It does not adjudicate all seven suspect review rows or close them.

The candidate queue has **723 rows**: the 718 original reasons remain, plus three
unmatched recovered works and two withheld source conflicts. Queue units mix
papers, author claims and institution strings; row totals are not error rates.

## Verification and limits

- **97 offline tests pass**. Cases cover Unicode distinctions, ordered bylines,
  immutable acquisition reuse, evidence hashes, held-out protection, source
  withholding, identity-gated reviewed triples, exact author-specific institutions
  and duplicate support. Offline structural validation passes; size validation
  returns 1 as expected. Lock consistency passes.
- Current candidate references **513 cached source objects**, all hash-verified.
  Twenty protected artifacts and all **5,046 legacy assignments** remain unchanged;
  zero acquired diagnostic papers overlap held-out groups.
- GROBID and both Neo4j HTTP endpoints return 200. Read-only checks on both
  databases return zero violations for all six integrity queries. Database content
  digests match task 006: original **154 / 211**, expanded **399 / 533**.
- Candidate base: `pilot-cdbd7165f817`; classified graph:
  `pilot-topic-7e3c90189547`. Graph SHA-256:
  `b78ecb704e356847b1066e01c70da5f1875f3f987bf1a0f57051b702765aa144`.
  Method/config/source hashes are in [the machine summary](evidence-review-v1.metrics.json).

Independent accuracy/recall remain unmeasured. Release size, all-ten-type and
coverage gates remain unmet. Fourteen conference editions remain unresolved;
ten MICCAI records lack official PDF URLs. Topics remain an uncalibrated draft
phrase baseline (87/248 papers labeled, 161 abstentions). Frozen test/audit samples
were not annotated or used for tuning. No models or GDS were installed.

Next: adjudicate the two source-version conflicts and identity/affiliation gaps
on development evidence; annotate development topics. Loading the candidate
requires an explicit migration or isolated instance. See [reproduction commands](../docs/evidence-review.md)
and [the work record](../docs/work-log/2026-11-04-001-evidence-review.md).
