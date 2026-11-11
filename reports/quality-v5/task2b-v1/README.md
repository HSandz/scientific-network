# Task2B: evidence-backed identity recovery

Start with the [measured report and recommendation](implementation-report.md).
Final development candidate is **`release-identity-v5-503aafe10a31`**.
It is separate from historical frozen v4 and the original v5 candidate-v3.
No promotion, DB import, application change, push or deployment occurred.

## Artifacts

| Artifact | Purpose |
| --- | --- |
| `doi-reconciliation.md`, `investigation/doi-ledger.json` | Seven cases, official/cached/Crossref evidence, decisions and withheld consequences |
| `identity-abstention-analysis.md`, `investigation/provider-classification.csv` | Exact classification of 170 IDs / 683 positions, uncertainty and recoverability |
| `investigation/provider-ledger.json`, `provider-context.json` | Names, ORCIDs, publication/affiliation/coauthor context and source locators |
| `investigation/alias-certificates.json` | Five public owner-declared alias crosswalk certificates; construction evidence |
| `external-request-ledger.json`, `alias-work-request-ledger.json` | Exactly 40 free public requests; timestamps, URLs, hashes and source roles |
| `evaluation-protocol.md`, `evaluation/` | Probability and diagnostic draws, blind packets, blank A/B assignments and sample/hash freeze |
| `candidate-v4-final/` | Final build manifest, comparison, ranks and structural validation |
| `comparison-final/` | Three-way metrics, exact recovery ledger, graph deltas, ranking stability, actual null semantic scoring |
| `validation-report.md`, `validation-receipt.json` | Tests, replay, hash checks, limitations and failures |
| `artifact-inventory.json` | Hashes for report files and ignored candidate output paths |
| `preservation-baseline.json` | 779 original file digests captured before source/resolver changes |
| `candidate-v4/`, `comparison/` | Preserved intermediate, superseded after report ordering fix; same acceptance counts |

Large original/candidate graph, decision/index/review ledgers, raw responses and
centrality score arrays remain ignored. Final graph and full decisions are under
`data/processed/identity-candidate-v5-release-v4-final/`; paths and SHA256 values
for every output are in `candidate-v4-final/candidate-manifest.json`. The graph is
not bundled into Git. A fresh clone requires restoring permitted, exact original
source/candidate inputs and verifying their frozen hashes, rather than silently
reacquiring current API data.

## Reproduce offline

From repository root, restore v4/v3 and the immutable source caches, then use new
unused output paths. Existing commands deliberately refuse overwrites/symlinks.

```bash
uv sync --locked --group dev --extra analysis --extra report
uv run pytest -q tests/test_identity_recovery_v5.py tests/test_mentions_v5.py tests/test_release_acquisition.py
uv run pytest

uv run python -m scientific_network.quality.recovery_investigation \
  --works data/interim/release-v1/works.jsonl \
  --decisions data/processed/identity-candidate-v5-release-v3/identity-decisions.jsonl \
  --requests reports/quality-v5/task2b-v1/external-request-ledger.json \
  --cache data/raw/identity-recovery-v5-release-v1 \
  --output reports/runs/task2b-manual-investigation

# Optional context inventory: same inputs, --context-only, unused JSON output.
# Reproduce the one frozen draw; do not choose a replacement sample based on labels.
uv run python -m scientific_network.quality.identity_evaluation \
  --decisions data/processed/identity-candidate-v5-release-v3/identity-decisions.jsonl \
  --output reports/runs/task2b-manual-evaluation

uv run python -m scientific_network.resolve.candidate_v5 \
  --config configs/identity-candidate-v5-release-v4-final.yaml \
  --output-dir reports/runs/task2b-manual-data \
  --report-dir reports/runs/task2b-manual-candidate
uv run research-network validate \
  --input reports/runs/task2b-manual-data/graph.json \
  --config configs/quality-release-v1.yaml --require-size \
  --output reports/runs/task2b-manual-structural.json

uv run python -m scientific_network.quality.recovery_comparison \
  --baseline data/processed/release-graph-v4/graph.json \
  --prior data/processed/identity-candidate-v5-release-v3 \
  --revised reports/runs/task2b-manual-data \
  --prior-report reports/quality-v5/candidate-v3 \
  --revised-report reports/runs/task2b-manual-candidate \
  --evaluation reports/quality-v5/task2b-v1/evaluation \
  --requests reports/quality-v5/task2b-v1/external-request-ledger.json \
    reports/quality-v5/task2b-v1/alias-work-request-ledger.json \
  --output reports/runs/task2b-manual-comparison
```

A second candidate build needs two further unused directories. All five data-output
hashes and `network-comparison.json` must agree. Comparison JSON agrees after
normalizing recorded output paths; location-dependent manifests are not claimed
byte-identical. The final code sorts reason-count keys before serialization.
Investigation ledgers/certificates replay exactly; the initial inventory summary
had arbitrary key order in its category-position map, now sorted (values unchanged).

The comparison module executes the missing-independent-reference scoring path
for v4/v3/revision. It does **not** synthesize gold labels. To score genuine later
references, use `identity_evaluation.score` / `paired_score` with adjudicated
independent references following `evaluation-protocol.md`; retain the original
blank assignments and frozen samples. Diagnostic draws stay separate.

## Targeted external evidence and cache replay

Original collection used the existing `SourceCache`, 15–20 second timeouts, one
attempt and bounded URL lists: 14 Crossref DOI records, 20 public ORCID person
records, five ORCID works lists and one official academic profile. All 40 succeeded.
No OpenAlex reacquisition, paid service, model download or crawler was used.
Profile works lists and the academic page provide investigation context; they do
not supply independent gold or permit inferred historical affiliations. Unknown
source-license metadata is preserved; full responses stay ignored.

To verify/replay these **existing cached requests** without network access:

```bash
uv run python -m scientific_network.collect.identity_recovery \
  --requests reports/quality-v5/task2b-v1/external-request-ledger.json \
    reports/quality-v5/task2b-v1/alias-work-request-ledger.json \
  --cache data/raw/identity-recovery-v5-release-v1 \
  --output reports/runs/task2b-manual-source-replay.json
```

This CLI accepts at most 40 explicitly listed public URLs on the three scoped
hosts and stops on access/quota failures. With absent cache objects it would issue
new public requests; restore historical bytes first for exact reproduction.
Updated API responses are a new source version, not a repair of the frozen cache.

Actual run commands/logs and intermediate failures are retained under ignored
`reports/runs/WORK-2026-11-11-004/`. The work entry records measured outcomes so
local-only console logs are not required to understand the result.
