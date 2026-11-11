# Artifact inventory

## Tracked implementation and configuration

| Path | Purpose |
| --- | --- |
| `src/scientific_network/quality/identity_audit.py` | Frozen-source baseline census and structural validation |
| `src/scientific_network/quality/pipeline_inventory.py` | Additional paper/topic/citation/guard inventory |
| `src/scientific_network/quality/candidate_network.py` | Paired centrality diagnostics |
| `src/scientific_network/resolve/mentions_v5.py` | Explicit mention states and source-backed decisions |
| `src/scientific_network/resolve/candidate_v5.py` | Isolated identity-only graph construction and comparison |
| `src/scientific_network/resolve/release.py` | Dictionary/string state bug fix; method v1.3 |
| `configs/identity-candidate-v5-release-v3.yaml` | Current candidate protocol and frozen input paths |
| `tests/test_mentions_v5.py`, `tests/test_identity_audit_v5.py` | Synthetic regressions and offline integration checks |

## Tracked reports and provenance

`reports/quality-v5/` contains the baseline Markdown/JSON, severity CSV, identity
error analysis, additive pipeline inventory, implementation/validation reports,
and reproduction entry point. `candidate-v3/` contains:

- `candidate-manifest.json`: source/config/code hashes and all candidate data hashes.
- `comparison.json`: counts, changes, remaining states, venue/year strata, preserved
  components and exact retained-position affiliation assertion.
- `network-comparison.json`: paired pivots, methods, top rankings and correlations.
- `quality-summary.json`: explicit official/matched/recovery denominators and null
  semantic metrics.
- `recovered-authorships.csv`: 15 recovered positions with decision IDs and cached
  evidence locators, without redistributing raw responses.
- `structural-validation.json`: actual offline CLI result and size checks.
- `reproducibility-receipt.json`: actual repeated hashes, runtime and preservation.
- `supplemental-preservation-v1.json`: additive historical recovery-membership and
  protected-directory membership checks; the earlier receipt stays unchanged.

`official-input-bindings-v1.json` additionally binds the original frozen roster
hash and all copied fields/DOIs to existing works; no corpus reconstruction.

Historical development runs: `candidate-v1/` (source `dfaa01b`, attribution issue)
and `candidate-v2/` (source `a3d4dd8`, before multiple-account safeguard). Their
configs and measured outputs remain intact; use matching source commits to replay.
The final implementation source checkpoint is `18f98d0`.

## Ignored local data

`data/processed/identity-candidate-v5-release-v3/` contains `graph.json`, the complete
`identity-decisions.jsonl`, `identity-index.json`, `review-queue.jsonl` and
`centrality-scores.json`. Every unresolved official mention remains in the decision
ledger. Index records preserve conflicting source observations and crosswalks.
These files are hash-bound by the tracked manifest and must not be force-added.

`reports/runs/WORK-2026-11-11-003/` contains source position/check ledgers, initial
preservation hashes, command/test logs, failed synthetic diagnostics, and separate
`replay-v3-data/` / `replay-v3-reports/` outputs. These are ignored. Original source,
graph and evaluation artifacts remain at their frozen paths, unchanged.

No new database, production deployment, public application artifact, model,
source download or full paper PDF was created. No Task 3–8 implementation.
