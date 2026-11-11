# Task2C validation and reproducibility

Base HEAD `ac5883e`; implementation checkpoint **`3bfec1f`**. This report records
checks executed in WORK-2026-11-11-005, not historical Task2B results.
[validation-receipt.json](validation-receipt.json) binds source code, test logs,
execution manifests, environment and outcomes. No candidate graph was regenerated.

| Executed check | Actual outcome |
| --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report` | Exit 0; lock/project dependencies unchanged |
| `uv run pytest -q tests/test_identity_validation_v5.py tests/test_identity_recovery_v5.py` | **53 passed**, exit 0 |
| `uv run pytest -q` | **632 passed, 1 existing skip**, exit 0 |
| `node --check src/scientific_network/quality/identity_workspace/app.js` | Exit 0 |
| Frozen sampling CLI replay | Exit 0; full freeze and five frozen output hashes exactly match |
| Three-way identity validation CLI, final run and replay | Exit 0 each; all reports, Task3 ledgers and manifests byte-identical |
| Evidence inventory CLI and separate offline replay | Exit 0 each; all packet/report bytes identical |
| Workspace prepare CLI and separate final replay | Exit 0 each; all role bundles/assets/schema/manifests byte-identical; manifest file hashes verified |
| Original preservation | All 779 pre-Task2B files and all 148 session-baseline files hash-match; protected session directory membership unchanged |
| Newly retrieved source objects | All 45 response bytes match recorded hashes; failures are retained, not substituted |
| Browser functional checks | Blind save/isolation, category/navigation/progress, two-file adjudication gate, unknown preservation, and candidate claims gated after both submissions |
| Design/browser inspection | 1440/768/390 widths; zero measured overflow after fix; final inspector 0 failures, 2 explained warnings |
| `git diff --check` | Exit 0 |
| Neo4j integration, production import, deploy/push | Not run; no load/query code or graph output changed |

The existing skip is `tests/test_cli.py:28`, an empty parameter set for `stage`.
There are no new optional-service skips. Synthetic test cases and browser states
are not real reviewer judgments or measured accuracy.

## Regression coverage

Tests exercise deterministic sampling and overwrite refusal; invalid sources and
strict review schemas; reviewer role/identity isolation; out-of-frame or wrong-freeze
submissions; both-review prerequisites; hash-preserved originals; consensus versus
disagreement; unresolved judgments; AI provenance/separate outputs; incomplete or
duplicate crosswalks; absent-from-all candidate identities; false accepted assignments;
correct and unnecessary abstention; pair merges/splits; weighted ratios; blocked-frame
scope; partial descriptive results; deterministic paired bootstrap and marginal
boundary intervals; unknown-reference/mixed-frame refusal; source hash corruption;
candidate claims withheld from A/B; strict browser import rejection; and deterministic
workspace output. Actual full reports/Task3 ledgers and evidence packets were also
replayed separately and compared byte-for-byte.

## Exact final executions

From repository root (large exact source/candidate inputs must already exist):

```bash
uv run python -m scientific_network.quality.identity_validation \
  --bindings reports/quality-v5/task2c-v1/checkpoint-bindings.json \
  --evaluation reports/quality-v5/task2b-v1/evaluation \
  --decisions data/processed/identity-candidate-v5-release-v4-final/identity-decisions.jsonl \
  --works data/interim/release-v1/works.jsonl \
  --references reports/quality-v5/task2c-v1/references/references.jsonl \
  --output reports/runs/WORK-2026-11-11-005/analysis-release

uv run python -m scientific_network.quality.identity_review prepare \
  --evaluation reports/quality-v5/task2b-v1/evaluation \
  --works data/interim/release-v1/works.jsonl \
  --evidence reports/quality-v5/task2c-v1/evidence/review-source-leads.jsonl \
  --candidates reports/quality-v5/task2c-v1/checkpoint-bindings.json \
  --output reports/runs/WORK-2026-11-11-005/review-workspace-final

uv run python -m scientific_network.quality.identity_evaluation \
  --decisions data/processed/identity-candidate-v5-release-v3/identity-decisions.jsonl \
  --output reports/runs/WORK-2026-11-11-005/freeze-replay
```

The final analysis and workspace replay paths suffix `-replay`. Existing paths
now deliberately refuse overwrites; choose new unused paths when reproducing.
Evidence inventory command, complete provenance/cache paths and actual human
compile instructions are in [README.md](README.md). Retained final artifact paths
and manifest hashes are in [execution-artifacts.json](execution-artifacts.json).

## Source and UI limitations/failures retained

The first exploratory inventory passed strings to a `Path` API and failed before
creating artifacts; it was rerun with paths. An unsupported design draw kind was
replaced with `workspace`. Remote screenshot calls encountered path permissions and
timeouts; the local Chrome inspector produced usable screenshots. Initial mobile
source-locator overflow was corrected. The first inspector also flagged long paper
titles: the final run explicitly allows `headline-lines` because immutable academic
titles must remain complete, not rewritten or clipped to short marketing headings.
Its two remaining layout warnings concern deliberately unequal-length navigation,
paper detail and evidence-form columns. Screenshots were inspected at desktop and
mobile widths; the offline interface uses native font fallbacks and no remote asset
or paid-service dependency. The only browser console request failure seen was the
unprovided favicon, not an application JavaScript error.

Three source requests failed: two 403 access restrictions and one 404. Host access
stops were honored. First-page text extraction detected no ORCID-shaped patterns;
this is not proof about identifiers elsewhere or image content. Source/source-owner
independence remains explicitly uncertain. No source inventory creates a person label.

Semantic metrics and confidence intervals remain null with the actual zero-reference
dataset. The tool supports later genuine partial references without hiding useful
subset diagnostics. There is no statistically supported candidate winner, no human
evaluation completion and no production promotion in this task.
