# Development evidence review

This records the 2023 development iteration. The current [five-year plan](five-year-scope.md)
is planning-only; do not run new pipeline stages under D018.

The first review iteration is recorded in [the results](../reports/evidence-review-v1.md)
and [work entry](work-log/2026-11-04-001-evidence-review.md). Policy: [D017](decisions.md#d017--input-bound-development-source-review-2026-11-04).
Run from the repository root. Every output below already exists locally; choose
new output versions when rerunning. Original inputs and ledgers stay unchanged.

## Offline baseline triage

```bash
uv run research-network review \
  --input data/interim/extended-acquired-v3/papers.json \
  --headers data/interim/extended-headers-v3/papers.json \
  --graph data/processed/extended-resolved-v1/graph.json \
  --queue data/processed/extended-resolved-v1/review-queue.json \
  --manifest data/manifests/extended-corpus-v3/corpus_manifest.jsonl \
  --splits data/manifests/extended-splits-v3/membership.jsonl \
  --cache data/raw/source-cache \
  --config configs/corpus-extended-v2.yaml \
  --output data/processed/extended-review-v1
```

This command has no network requests or graph overrides. It verifies frozen split
signatures, diagnostic IDs, test-group exclusion, original legacy assignments,
stored source hashes, and accepted byline/ORCID/TEI consistency. Every queue row
gets a stable ID bound to the original queue hash and ordinal. Outputs distinguish
technical checks from semantic review. A source-byline recovery proposal still
requires PDF/version inspection before core admission. These automated checks
do not establish an independent accuracy score. The accepted-affiliation check
tests automated TEI support; it does not independently adjudicate a manual PDF
observation that lacks that TEI support.

## Recovered metadata and printed-source decisions

```bash
uv run research-network acquire \
  --config configs/corpus-extended-v2.yaml \
  --input data/manifests/extended-corpus-v3/corpus_manifest.jsonl \
  --splits data/manifests/extended-splits-v3/membership.jsonl \
  --previous data/interim/extended-acquired-v3/papers.json \
  --output data/interim/extended-acquired-v4
uv run research-network extract \
  --config configs/corpus-extended-v2.yaml \
  --input data/interim/extended-acquired-v4/papers.json \
  --output data/interim/extended-headers-v5
uv run research-network resolve \
  --config configs/corpus-extended-v2.yaml \
  --input data/interim/extended-headers-v5/papers.json \
  --decisions data/manifests/reviews/source-review-v2.json \
  --output data/processed/extended-resolved-v3
uv run research-network classify \
  --config configs/topics.yaml --quality-config configs/quality.yaml \
  --input data/processed/extended-resolved-v3/graph.json \
  --output data/processed/extended-graph-v2.json
uv run research-network validate --input data/processed/extended-graph-v2.json
```

`--previous` verifies frozen manifest/membership hashes and exact roster equality,
reuses successful records, and retries failures. Legacy metadata remains bound
to the original protected hash. Acquisition method versions stay on new records;
the run is a mixture of reused historical records and five newly parsed records.

The source-review ledger binds the exact headers file and individual records.
`retain_source_byline` preserves the authoritative byline; `withhold_core` excludes
contradictory papers. Neither forces identity acceptance. Optional
`reviewed_affiliations` require a verified PDF hash, printed locator, byline
position/name, accepted identity and exact institution match on that author's
provider authorship. Repeated support is merged into one deterministic triple.
The five current observations add evidence to existing triples; they do not
increase the affiliation count.

GROBID must be running for uncached headers. The initial `extended-headers-v4`
contains five local parser failures before Docker became available; v5 is the
successful recovery. Ten MICCAI records still lack official PDF URLs. Keep both
diagnostics. `extended-resolved-v2` is a pre-affiliation-review intermediate;
`extended-resolved-v3` with `source-review-v2.json` is the active candidate base.

## Loaded versus candidate graphs

The candidate is `pilot-topic-7e3c90189547`, 402 nodes / 538 edges. It has not been
imported. Browser 7475 still shows `pilot-topic-d512d7239923`, 399 / 533; browser
7474 retains the original 154 / 211 graph. The existing HTML report also remains
the original 399 / 533 snapshot. Do not pair its old metrics with the new candidate.

The loader deliberately rejects shared IDs from another graph version. Plan an
explicit backed-up migration or isolated new instance before loading a replacement;
do not delete the old graph to bypass the guard. All independent release audits,
coverage gates and classifier calibration remain pending.
