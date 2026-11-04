# Data contracts and storage

Raw sources are immutable. Each stage writes new versioned outputs and a summary
with input/config hashes, method version, success/failure states and timestamp.
Use Parquet for typed canonical tables and JSONL for evidence/review events.
The initial `GraphArtifact` JSON model is a small offline interchange/fixture format,
not a replacement for all stage tables or a completed production data model.

Current discovery/splits write immutable JSONL and Parquet mirrors. Other pilot
stages write immutable JSON records and a `GraphArtifact`, including affiliation
observations, edge evidence and a separate review queue. The full set of normalized
Parquet tables below remains the production target. Source-cache request metadata
and content-addressed raw objects support pilot acquisition/resume; failed pilot
records are explicit rather than silently removed from the official corpus ledger.

| Location/table | Key | Minimum fields and policy |
| --- | --- | --- |
| `data/manifests/sources.yaml` | source_id | Configured source URLs and roles; not a fetched roster |
| `corpus_manifest.parquet` | official_record_id | venue, year, track, official/PDF URLs, title, decision/status, exclusion reason, retrieval reference |
| `retrieval_log.jsonl` | request_id + attempt | source, URL, time, status, attempt, raw path/hash, parser version, terminal state |
| `paper_records` | paper_id | selected official record/title/abstract, venue/year/track, core flag, external-ID crosswalk, version decisions |
| `author_mentions` | mention_id | paper_id, raw name, byline order, source locator |
| `affiliation_mentions` | mention_id | paper_id, raw string, marker/alignment evidence, source locator |
| `reference_mentions` | reference_id | citing paper, raw reference, locator, target candidates and resolution status |
| `researchers` | researcher_id | display name, aliases, verified crosswalks, resolution state, identity evidence |
| `organizations` | organization_id | canonical name, raw aliases, sector/unknown, optional ROR/location, normalization decisions |
| `authorships` | researcher_id + paper_id | byline position, mention_id, accepted evidence |
| `affiliation_observations` | researcher_id + paper_id + organization_id | raw mention, explicit alignment/marker evidence, review state |
| `paper_topics` | paper_id + leaf_topic_id | supporting text, method/model/taxonomy version, score kind, decision band, evidence |
| `citations` | citing_id + cited_id | reference locator, verified target-match evidence, core/context status |
| `edge_evidence` | evidence_id | kind, source URL/record, retrieval timestamp, SHA-256, source-field/TEI/page locator, excerpt |
| `edges` | deterministic edge_id | predicate, semantic endpoints, evidence IDs, method/graph version, accepted status |
| `derived_support` | edge_id + support record | exact base edges, distinct paper IDs, raw count, fractional contribution |
| `review_queue/history` | decision_id | candidates/conflict, reason, reviewer, evidence, timestamp, reversible accepted decision |

The corpus ledger must reconcile included, excluded, failed, pending and unresolved
official records. Missing enrichment does not remove an accepted proceedings paper.
Inspect and resolve unknown tracks instead of silently classifying them as main.

## Expanded-scope planning registry

`configs/conference-scope-2021-2025.yaml` lists 34 series, five years and 170
venue–year review candidates with unverified status, catalog leads and track
policies. It is not an executable corpus manifest and authorizes no pipeline work
or collection. `configs/conference-scope.yaml` is the unchanged historical 2023
registry. No confirmed five-year edition count is asserted. Future ledger keys must be edition-qualified
(e.g. venue + year + official record ID) because IDs can collide across publishers.
Track no-edition/unavailable/review states separately from paper exclusions.
Preserve the original pilot tables; new scope, split, taxonomy and graph versions
need fresh paths and explicit crosswalks. See [the scope policy](conference-scope.md).

## Small graph artifact

`src/scientific_network/contracts.py` defines:

- Root: `schema_version`, `graph_version`, explicit `is_synthetic`, `nodes`, `edges`,
  `evidence`, and `affiliation_observations`.
- Node: `id`, one of five `label` values, `name`, domain `properties`.
- Edge: `edge_id`, `relation`, `source_id`, `target_id`, `evidence_kind`, nonempty
  `evidence_ids`, `method_version`, `graph_version`, accepted status, `properties`.
- Source evidence: URL, timezone-aware retrieval time, 64-digit lowercase SHA-256,
  locator; inferred topics also require a supporting excerpt.
- Derived evidence: nonempty `support_edge_ids` and `support_paper_ids`. Validation
  recomputes derived inventories, support ledgers/counts and fractional weights
  whenever derived edges are present; base-only graphs can be checked separately.
- Affiliation observation: ID, researcher, paper, organization and observed evidence.

The validator checks referenced records, endpoint labels, IDs, duplicates,
orientation, source evidence classes, paper/venue invariants, topic levels and
author-specific affiliation support. It cannot prove that the source claim or an
identity merge is correct. It does not fetch URLs or recompute actual raw-file hashes.

## Git boundary

Track small source/corpus manifests and reviewed permitted release metadata.
`data/raw/`, `interim/`, `processed/`, `annotations/`, generated figures and run
logs are ignored initially. Promote a release artifact explicitly only after
checking size, permitted redistribution and sensitive fields; include version/hash
metadata and rebuild instructions. Do not use forced adds as a substitute for review.

Keep PDFs, credentials, local DBMS volumes, private annotations/profiles and models
out of Git. Export minimal permitted supporting excerpts. Code licensing and
third-party source licensing are separate decisions.

## Expanded diagnostic additions

The expanded workflow writes an all-series `edition-ledger.jsonl/.parquet`, with
collected/legacy, unresolved/blocked and no-edition states plus source records. A
partial page cannot admit an edition to supplemental sampling. Corpus and split
summaries bind manifest, corpus, quality, membership and predecessor hashes.

Paper `topic_text_evidence_id` points to the graph evidence record for the official
text source. It is distinct from the roster evidence supporting R3; topic literal
spans must not be attributed to an index that lacks the abstract. This is a
technical evidence pointer, not a sixth entity label or counted domain node.

Official record IDs remain edition-qualified. Identical DOM repetitions collapse;
conflicting official records and shared matched provider works require review.
Normalized titles group potential leakage only, never establish work/person identity.
The current [workflow](extended-workflow.md) and [report](../reports/extended-v1.md)
identify active versions; older outputs remain reproducibility/diagnostic artifacts.
