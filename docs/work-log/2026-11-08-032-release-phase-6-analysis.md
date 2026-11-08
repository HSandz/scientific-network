# WORK-2026-11-08-032 — Release Phase 6 analysis

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-08 13:05 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-2026-11-08-031](2026-11-08-031-release-neo4j-loads.md) |
| Git state | `main` at `ecb7874`; clean at start |

## Objective

Continue Phase 6 from the frozen and loaded graph v2. Run the configured analysis, identify
gaps against D040, and produce measured analysis outputs, figures and evidence-backed
business findings without making semantic accuracy claims.

## Changes and findings

- P4 and P5 database checks are complete; `neo4j-five-year` contains graph
  `release-5d830ffcbdf4` and remains healthy.
- Verified the v2 graph hash is `b79e456b22488ca8f753fb0884afd5c6a89afeeeaffec07d89ce83b2c5c141fb`,
  matching `graph-v2-summary.json`; it contains 52,415 nodes and 275,438 edges.
- Added D040 release metrics for yearly papers/researchers/new collaboration pairs,
  sector and country-pair mixing, fractional topic shares by year/venue, in-scope
  cited papers, bridge researchers with community topic profiles, and source-paper
  candidate tables for the three planned business cases.
- Added a standalone renderer for the six planned PNG/CSV figure pairs and a
  versioned caption index. Topic outputs remain explicitly provisional pending
  human review; missing country codes stay visible as `UNKNOWN`.
- Added [Phase 6 findings](../../reports/release-v1/findings.md): three bounded
  findings with linked supporting papers and two shortlists with explicit
  screening criteria. Betweenness candidates are flagged as unstable under the
  frozen strict-evidence sensitivity check.
- Final v2 analysis completed in 2m17s with 2,302,812 KiB maximum RSS and no
  swapping. All planned figures were regenerated after correcting the country
  pair matrix orientation and making community labels legible.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis` | passed, exit 0 | `reports/runs/WORK-2026-11-08-032/uv-sync.log` |
| Full suite before changes: `uv run pytest` | 354 passed, 1 skipped, exit 0 | `reports/runs/WORK-2026-11-08-032/pytest-before.log` |
| Focused: `uv run pytest tests/test_analysis.py tests/test_analysis_release_metrics.py -q` | 11 passed, exit 0 after correcting the expected aggregated unknown-country count | analysis unit tests |
| `uv run python -m scientific_network.analysis.figures --help` | passed, exit 0 | CLI help |
| Final `uv run pytest` | 357 passed, 1 skipped, exit 0 | `reports/runs/WORK-2026-11-08-032/pytest-final.log` |
| `uv run research-network analyze --input data/processed/release-graph-v2/graph.json --config configs/analysis-release-v1.yaml --quality-config configs/quality-release-v1.yaml --output reports/release-v1/analysis.json` | passed, exit 0; 2m17s; max RSS 2,302,812 KiB; 0 swap | analysis v2, graph SHA-256 `b79e456b22488ca8f753fb0884afd5c6a89afeeeaffec07d89ce83b2c5c141fb`; analysis SHA-256 `252afe8787c1e872dda47c27bd15a36b74387a208ee3d0b79263632ee721cd0d` |
| `uv run python -m scientific_network.analysis.figures --analysis reports/release-v1/analysis.json --output-dir reports/final-report/figures` | passed, exit 0; six PNG/CSV pairs and caption file | `reports/final-report/figures/` |
| Phase 6 exit review | all four size gates pass; 13,617 papers reconcile across years; topic coverage 11,575/13,617; analysis remains `not_certified` | `reports/release-v1/analysis.json`, `findings.md` |

## Decisions

Follow D040's defined projections and business question framing; report only statistics
computed from the frozen v2 graph and identify any evidence limits.

## Open issues and limitations

Human semantic review is still required. Topic labels are inferred and pending
review; overall strict-filter retention is 8.0% for researcher collaboration,
27.4% for organization collaboration, 0% for citations and paper topics, and
100% for organization topics. Betweenness top-20 overlap is 1/20 under the
strict filter. Citation counts are not exposure-time normalized. No human
accuracy claim is made.

## Next step

Proceed to Phase 7: freeze graph/config hashes, generate the edge review packet,
verify the prediction-blind topic sheet, and start the report methods sections.

## Corrections

None.
