# Versioned graph analysis

`research-network analyze` validates a graph artifact, builds the five named
projections from `configs/analysis.yaml`, and writes descriptive metrics. The
projection contents and scores are deterministic for the same graph and config;
the run timestamp changes. Existing outputs are never overwritten.

```bash
research-network analyze \
  --input data/processed/final-graph.json \
  --config configs/analysis.yaml \
  --quality-config configs/quality.yaml \
  --readiness reports/final/post-build-audit-readiness.json \
  --output reports/final/analysis-v1.json
```

The projections are researcher collaboration (`COAUTHORED_WITH`), organization
collaboration (`COLLABORATED_WITH`), directed core citations (`CITES`), paper-topic
assignments (`HAS_TOPIC`), and organization-topic contributions
(`CONTRIBUTES_TO_TOPIC`). Configured fractional weights are used where present;
otherwise edges have unit strength. The report includes degree/strength, density,
components, isolates and centrality rankings. Betweenness uses inverse positive
edge strength as distance. Citation PageRank uses a deterministic power iteration
with damping 0.85. Seeded Louvain communities run only on the two collaboration
projections, using the configured seeds and resolutions; the configured NetworkX
fallback is used, not GDS.

The synthetic fixture is allowed for protocol checks and always returns
`synthetic_protocol_only` with `release_status: ineligible_synthetic`. It cannot
support research claims. A non-synthetic graph additionally requires all
configured size gates, a readiness receipt matching its graph version and hash,
and an analysis config marked `frozen`. That config must include a frozen
`robustness.strict_evidence_filter` using one or more implemented criteria:

- `minimum_evidence_records`: minimum number of provenance records on each edge;
- `minimum_support_count`: minimum edge `support_count`;
- `allowed_evidence_kinds`: subset of the schema evidence classes;
- `exclude_method_versions`: methods to omit.

No thresholds are supplied by the tool. Project owners must freeze them before a
real analysis. The output reports baseline and filtered metrics, edge retention,
largest-component share, top-k overlap, and Spearman rank correlation on common
nodes. A real run is still labeled `analysis_metrics_only` and is not a quality or
release certificate.

Unimplemented work remains explicit: component `evaluate`, recall and coverage,
citation-age comparisons, figure generation, sector/topic portfolios, source-backed
business findings and their supporting-paper review. The current run on
`tests/fixtures/synthetic_graph.json` is only a software protocol exercise.
