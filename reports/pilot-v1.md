# First live pilot — 3 November 2026

**A diagnostic pilot, not a certified release.** Graph `pilot-topic-0bb7f11a404e` has
154 nodes and 211 edges. The full official ledger has
5,046 eligible main papers (3,218 NeurIPS; 1,828 ICML), plus 322 excluded NeurIPS
Datasets and Benchmarks records. Only 100 papers have been processed into this graph.

The frozen pilot contains 50 papers per venue, includes the 60 development papers,
and excludes all 120 held-out test papers. Selection is deterministic and venue-balanced;
difficult-layout stratification has not been independently checked.

## Measured inventory

| Node label | Count |
| --- | ---: |
| Organization | 4 |
| Paper | 100 |
| Researcher | 28 |
| Topic | 20 |
| Venue | 2 |

| Predicate | Count |
| --- | ---: |
| AUTHORED | 28 |
| AFFILIATED_WITH | 5 |
| PUBLISHED_IN | 100 |
| CITES | 0 |
| HAS_TOPIC | 53 |
| SUBTOPIC_OF | 16 |
| COAUTHORED_WITH | 8 |
| COLLABORATED_WITH | 1 |
| RESEARCHES_TOPIC | 0 |
| CONTRIBUTES_TO_TOPIC | 0 |

| Evidence class | Count |
| --- | ---: |
| curated_taxonomy | 16 |
| derived | 9 |
| inferred_topic | 53 |
| observed | 133 |

Only **133 R1–R4 factual edges** count toward the 5,000-edge gate. Seven predicates
are nonempty. No verified within-pilot citations or above-threshold researcher/organization
topic profiles were found; absent support was not fabricated.

## Coverage and extraction

- Abstract availability: **100/100**; strict OpenAlex work matches: **61/100**.
- Valid TEI responses: **100/100**; papers with extracted affiliation structures:
  **51/100**. Valid XML does not establish correct author/affiliation extraction.
- Resolved authorship coverage: **28/464 (6.03%)**
  official author–paper slots, representing **28 distinct resolved researchers**.
- Accepted affiliation coverage: **5/464 (1.08%)**
  author–paper slots, with **5 aligned triples**.
- Topic paper coverage: **40/100 (40%)**; 53 leaf assignments and 60 abstentions.

| Venue | Author–paper slots | Matched works / papers | Resolved authorships | Affiliated author–paper pairs | Papers with TEI affiliations | Topic-labeled papers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| venue:icml | 222 | 29/50 | 15 | 5 | 12 | 19 |
| venue:neurips | 242 | 32/50 | 13 | 0 | 39 | 21 |

PDF payloads total **437,835,764 bytes (437.84 MB decimal)**; median PDF size is
1,619,295 bytes. The corrected run's summed record durations are **736.93 seconds**.
Some PDFs were reused from the interrupted first run, so this is neither a cold-run
benchmark nor a full-corpus estimate. One service snapshot showed about 3.2 GiB
GROBID memory and 0.93 GiB Neo4j memory on an 11.68 GiB host; these are not peaks.
Human annotation time is unmeasured.

## Verification and limitations

Structural validation passed. Neo4j first import went from 0 to 154 nodes and 211
edges. Unchanged replay retained those counts. Six integrity queries returned zero
violations; a conflicting-version import was rejected without changing graph data.
All 429 referenced source objects passed SHA-256 checks. Enforcing release size
gates deliberately fails (exit 1): researcher, factual-edge and ten-type targets
are unmet. Structural checks and source hashes do not measure semantic accuracy.

Identity resolution currently requires public ORCID publication corroboration.
Institution matching requires exact printed names and author-specific metadata.
These policies leave substantial unresolved coverage. The review queue contains
39 unmatched works, 138 uncorroborated ORCID-publication cases, 121 missing/ambiguous
identifier cases, 16 institution candidates and one missing/ambiguous PDF-author
alignment. These are different review units, not disjoint paper counts.
Topics use an uncalibrated phrase baseline and draft taxonomy. Context/exclusion
handling and human labels remain necessary. No independent precision, recall, F1
or course accuracy claim has been measured. No release threshold has been lowered.

## Review and reproducibility

The local, ignored `data/annotations/pilot-affiliation-review-v1.csv` has 20 diagnostic rows with blank reviewer
fields: five automatically accepted triples and 15 unresolved institution candidates.
It is a targeted pilot diagnostic packet, not the independent release audit. Both
reviewers should inspect official PDF/TEI markers, record decisions and seconds
independently, then adjudicate using [the annotation guide](../docs/annotation-guide.md).

Commands and immutable output conventions are in [the pilot workflow](../docs/pilot-workflow.md).
The [machine-readable metrics](pilot-v1.metrics.json) preserve full input/config hashes,
method versions and denominators. The [task record](../docs/work-log/2026-11-03-004-discovery-pilot-graph.md)
records failures, exact checks and the handoff. Raw downloads, graph payloads,
review packet and console logs remain local and ignored.

Next: review the packet and development identities, improve conservative work/
institution resolution and substantive topic coverage, then rerun on development
data before scaling. Keep held-out IDs untouched. Analysis/evaluation automation,
canonical production Parquet exports, independent auditing and GDS remain pending.
