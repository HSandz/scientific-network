# WORK-2026-11-07-015 — Offline named-projection analysis stage

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 21:59 +07:00; updated 2026-11-07 15:12 +00:00 / 22:12 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-014](2026-11-07-014-p09-offline-contracts.md) |
| Git state | main at 66e692d; extensive pre-existing uncommitted work preserved |

## Objective

Advance the P09 analysis-tooling work independently of the blocked P01 sources and
P02 capacity. Implement deterministic named graph projections and basic analysis
summaries for structurally valid synthetic fixtures, and require a matching
post-build receipt plus a frozen analysis configuration before running on a
non-synthetic graph. Do not produce business findings or release claims from
synthetic data.

## Changes and findings

- Implemented `research-network analyze` for the five configured projections.
  It structurally validates the graph, preserves projection direction and
  strengths, reports components/degree/centrality, uses dependency-free
  power-iteration PageRank, and runs configured seeded Louvain communities on
  researcher/organization collaboration projections.
- A frozen strict evidence filter can produce baseline-versus-filtered results,
  edge retention, top-k overlap, Spearman rank correlation and largest-component
  share. Non-synthetic analysis requires all configured graph-size gates, a
  matching post-build readiness receipt, and frozen analysis/filter settings.
  Outputs refuse overwrite and label synthetic runs `synthetic_protocol_only`.
- Added [analysis workflow documentation](../analysis.md). The existing config
  remains proposed; no threshold or evidence policy was changed. No dependency or
  lockfile change was needed. `evaluate`, citation-age/coverage analysis, figures,
  portfolios and source-backed business findings remain incomplete.
- A fresh local DNS check still fails for all 12 official/Sites hosts rechecked.
  The web viewer can render official AAMAS pages, but they do not add the complete
  local source capture and identifier evidence needed to change its disposition.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Read current status, roadmap, pregraph plan, analysis/evaluation configuration, graph contracts and current P01/P02 work logs | completed; `analyze` is a placeholder and the analysis filter is unfrozen | `docs/status.md`, `docs/roadmap.md`, `docs/pregraph-completion-plan.md`, `configs/analysis.yaml`, `src/scientific_network/contracts.py`, WORK-013/014 |
| Initial `UV_CACHE_DIR=/tmp/uv-cache-work015 uv run research-network analyze --input tests/fixtures/synthetic_graph.json --config configs/analysis.yaml --output reports/runs/WORK-2026-11-07-015/synthetic-analysis-v1.json` | failed (1); NetworkX PageRank required unavailable optional SciPy | No output was written; replaced with deterministic power iteration and added coverage |
| `UV_CACHE_DIR=/tmp/uv-cache-work015 uv run pytest tests/test_analysis.py tests/test_cli.py -q` | passed (0); 10 tests | `tests/test_analysis.py`, pending-stage behavior for `evaluate` |
| `UV_CACHE_DIR=/tmp/uv-cache-work015 uv run pytest -q` | passed (0); 216 tests in 3.71 s | Full configured offline suite |
| `python -m py_compile src/scientific_network/analysis/analyze.py src/scientific_network/cli.py src/scientific_network/pipeline.py` | passed (0) | Changed Python modules compile |
| `UV_CACHE_DIR=/tmp/uv-cache-work015 uv run research-network analyze --input tests/fixtures/synthetic_graph.json --config configs/analysis.yaml --output reports/runs/WORK-2026-11-07-015/synthetic-analysis-v2.json` | passed (0); `synthetic_protocol_only`, `ineligible_synthetic`; method `named-projection-analysis-v1`; no research result | Ignored run artifact; graph SHA-256 `fde1dc302d66ee28e045cd4ae9d74238315f631ade95932cdaef91453d14dc2c`; analysis-config SHA-256 `46d2d78bb08909c078d6de495f1ccfc843dde5c68bc47efaaf3cdaa9df404e2c` |
| Frozen strict-filter sensitivity test on the synthetic fixture | passed; baseline/strict projection tables and comparisons generated; research/release status remains synthetic-only | `tests/test_analysis.py`; no research filter thresholds adopted |
| Non-synthetic readiness/frozen-config gate test | passed; unfrozen settings rejected before an output file is created | `tests/test_analysis.py` |
| `socket.getaddrinfo` for 12 official/Sites hosts | failed for all 12 with temporary name-resolution failure | P01 source access remains unavailable; no roster or frozen input changed |
| `git diff --check` and whitespace/local-link scan | passed; no whitespace defects and all local links resolve in updated Markdown | Task docs, roadmap, status, local Site report and README |

## Decisions

None. The analysis configuration, graph scope and evaluation thresholds remain
unchanged.

## Open issues and limitations

No real graph or research result exists. The analysis module implements projection
metrics and filter sensitivity only; it does not implement citation-age/coverage,
figures, portfolios, or source-backed findings. The current analysis config is
still proposed. P01 remains incomplete and P02 remains no-go. Real-graph analysis
has not run.

## Next step

Continue P09 with the component evaluation contract described in
[`evaluation.md`](../evaluation.md), preserving the nonzero `evaluate` stage until
its held-out inputs, adjudication and coverage requirements are supported. Keep
business findings, final graph work and release certification pending.

## Corrections

None.
