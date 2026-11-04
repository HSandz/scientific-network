# Historical NeurIPS/ICML pilot workflow and current implementation limits

**Historical 2023 pilot.** The current target is [2021–2025](five-year-scope.md);
pipeline implementation/collection are paused under D018. Commands below document
reproduction of old artifacts, not authorization to run a new corpus.

These are **historical two-venue commands and output paths**. Expanded collection
is now authorized under D015; follow the [expanded workflow](extended-workflow.md)
for current config, outputs and separate database. Preserve the frozen legacy
outputs: newer method versions need fresh output directories. Do not pass the
planning registry to pipeline commands.

Run from the repository root after `uv sync --locked --group dev`. Put credentials
in ignored `.env` or environment variables. Existing process variables take
precedence. Keys/passwords are never part of public source-cache descriptors.

## Official roster and frozen splits

```bash
uv run research-network discover --config configs/corpus.yaml --output data/manifests/corpus-v1 --cache data/raw/source-cache
uv run research-network split --input data/manifests/corpus-v1/corpus_manifest.jsonl --config configs/quality.yaml --corpus-config configs/corpus.yaml --output data/manifests/splits-v1
```

Discovery retains included, excluded and unknown-track review rows. It uses explicit
NeurIPS track labels and the official PMLR 202 roster, never a shared-proceedings
assumption. IDs are anchored to official records. Both JSONL and Parquet are written.
The initial live roster contained 5,046 main papers and 322 excluded Datasets and
Benchmarks papers; this is discovery metadata, not a completed research graph.

Splits use a fixed seed and normalized-title leakage groups. This grouping protects
against evaluation leakage; it is not proof that equal titles establish work identity.
Reserve 60 test and 30 development papers per venue. The 50-per-venue pilot includes
the development subset and excludes test groups. Duplicate versions that change
requested counts require reconciliation instead of silent resampling.

## Metadata acquisition

```bash
uv run research-network acquire --input data/manifests/corpus-v1/corpus_manifest.jsonl --splits data/manifests/splits-v1/membership.jsonl --config configs/corpus.yaml --output data/interim/pilot-v1 --cache data/raw/source-cache
```

The frozen manifest, membership and corpus-config hashes are checked before fetching.
Every pilot paper retains its official title, full citation-metadata byline, abstract,
PDF link and source record. OpenAlex candidates must match normalized title, year
window and the complete ordered byline. DOI/official URL evidence disambiguates
otherwise equal candidates. The accepted work can be a matched preprint version;
official proceedings remain the scope authority. Conflicts remain unresolved.

The user key is loaded at command invocation; access/quota errors stop collection.
Immutable per-paper successes and raw responses support resume after interruption.
Changing an input/config requires a fresh output version; never edit frozen artifacts.
Failed acquisition records are explicit and make the acquisition command return nonzero.

## Scientific header extraction

```bash
docker compose --profile nlp up -d grobid
uv run research-network extract --input data/interim/pilot-v1/papers.json --config configs/corpus.yaml --output data/interim/pilot-headers-v2 --cache data/raw/source-cache
```

The pinned parser is GROBID 0.8.2 CRF-only. Download each pilot PDF, verify it starts
with a PDF signature, and call `processHeaderDocument` with external consolidation
disabled and `Accept: application/xml` explicitly requested. Reject non-TEI
responses. Preserve PDF/TEI hashes, author nesting, affiliation locators, sizes and
record processing time. Parse failures stay in review; zero parsed headers is a
blocking failure. Header extraction is not a full-reference extraction pipeline.

## Conservative resolution and topic baseline

```bash
uv run research-network resolve --input data/interim/pilot-headers-v2/papers.json --config configs/corpus.yaml --output data/processed/pilot-resolved-v1 --cache data/raw/source-cache
uv run research-network classify --input data/processed/pilot-resolved-v1/graph.json --config configs/topics.yaml --quality-config configs/quality.yaml --output data/processed/pilot-graph-v1.json --cache data/raw/source-cache
uv run research-network validate --input data/processed/pilot-graph-v1.json --config configs/quality.yaml --output reports/runs/pilot-validation.json
```

Current researcher resolution requires an unambiguous provider-linked ORCID and a
public ORCID publication title/identifier corroborating the exact matched work.
Provider conflicts, common-name-only matches and missing corroboration go to the
review queue. This deliberately limits coverage; it is not the complete eventual
non-ORCID resolution method. Official papers remain even if all authors are unresolved.

An affiliation needs a uniquely aligned TEI author and exact printed-institution
name matching that author's work-specific OpenAlex institutions. Current profile
employment is never used. Preserve each researcher–paper–organization observation
before aggregating R2. Institution aliases/rollups and uncertain assignments need review.

The topic method is an **uncalibrated phrase baseline**, using literal title/abstract
spans and the draft 16-leaf taxonomy. It abstains on no support or more than three
candidate labels. It does not claim the phrase is substantively central or that
95% precision/80% coverage has been achieved. No embedding model was downloaded.

R7–R10 are recomputed from accepted core support. Coauthor fractional denominators
use the full official byline even when some authors remain unresolved. Organization
pairs need distinct authors and exact paper-specific observations. Counts, support
ledgers and fractional weights are checked again by structural validation.

## Neo4j import and repeatability

```bash
uv run research-network build --input data/processed/pilot-graph-v1.json --config configs/quality.yaml --output reports/runs/pilot-import.json
uv run research-network build --input data/processed/pilot-graph-v1.json --config configs/quality.yaml --output reports/runs/pilot-import-replay.json
```

The importer creates constraints, checks ownership/version conflicts, then loads
and reconciles counts within a transaction. Repeated unchanged input must not grow
the graph. It refuses a reused report path before DBMS writes. Existing foreign or
different-version IDs are not overwritten. A new graph version sharing entity IDs
needs a separate database or an explicitly reviewed migration; automatic replacement
is not implemented. Evidence stays in the versioned JSON ledger, referenced by edges.

The first live graph is `pilot-topic-0bb7f11a404e`: 154 nodes and 211 edges, with
unchanged replay verified. [The pilot report](../reports/pilot-v1.md) and
[metrics](../reports/pilot-v1.metrics.json) preserve measured coverage, input hashes
and limitations. A local unannotated 20-row diagnostic packet is at
`data/annotations/pilot-affiliation-review-v1.csv`; use separate reviewer copies
and retain original decisions/timing before adjudication. It is not a release audit.

Every import report explicitly labels this as an uncertified pilot. Full-corpus size,
all ten nonempty predicates, independent accuracy/recall/coverage, two-person annotation,
complete identity/alias resolution, citation verification and final SNA remain release
work. `analyze` and `evaluate` remain explicit nonzero-returning placeholders.
