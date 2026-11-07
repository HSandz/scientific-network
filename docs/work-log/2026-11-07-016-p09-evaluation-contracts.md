# WORK-2026-11-07-016 — P09 evaluation contracts

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 22:16 +07:00; updated 2026-11-07 22:42 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-015](2026-11-07-015-offline-analysis-stage.md) |
| Git state | main at 66e692d; extensive prior uncommitted project work preserved |

## Objective

Continue the pregraph completion plan's offline P09 work. Repair deterministic
strict-filter provenance in the analysis output, then implement only evaluation
contracts supportable with synthetic or otherwise permitted offline inputs.
Do not manufacture human labels, claim independent accuracy, change thresholds,
or unblock P01/P02 without their required evidence.

## Changes and findings

- Started from WORK-015's analysis implementation; its result builder called a
  missing `_strict_filter_hash` helper. Added canonical JSON hashing and tests for
  both absent and configured filter values.
- Read the current P09 plan, evaluation protocol, status and work-log history.
  P01 remains incomplete; P02 has one reported reviewer with unknown hours and a
  second independent reviewer unconfirmed.
- Added `research-network evaluate` and `evaluation/components.py`. The command
  binds predictions and two reviewed gold packets to an exact frozen frame and
  quality-config hash; validates evidence locators, adjudications and declared
  timestamps; and reports weighted/unweighted P/R/F1, per-stratum counts, topic
  macro/per-label scores, pairwise resolution errors, reviewer agreement and
  eligible-core coverage. Synthetic outputs are protocol-only. Real scores still
  require frozen quality settings, a reserved test frame and a complete release
  coverage denominator. The tool does not verify reviewer independence or split
  membership/leakage against the canonical manifest.
- Refreshed the evaluation protocol, roadmap, status, task plan and local Site
  Report. The v10 output audit confirms 42/42 manifest hashes and preserves
  98/10/22/40 edition statuses, 76,629 assignments and 1,095 tests.
- Sites `get_site` confirmed the same active public project at version 18 and the
  existing URL/audience. After the user's explicit authorization, supplied a
  fresh short-lived credential only to the supported helper's hidden stdin. The
  helper failed before checkout because `git.chatgpt-team.site` did not resolve;
  the credential was not written to disk or logged. No source audit, build, push
  or deployment occurred.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Initial repository/state and contract inspection | completed; no edits to roster, splits, enrichment or graph state | `docs/pregraph-completion-plan.md`, `docs/evaluation.md`, WORK-013–015 |
| `UV_CACHE_DIR=/tmp/uv-cache-work016 uv run pytest tests/test_component_evaluation.py tests/test_analysis.py tests/test_cli.py -q` | passed (0); final focused rerun 12 passed, 1 skipped in 0.35s | `tests/test_component_evaluation.py`, analysis provenance checks; CLI parameterized pending-stage case skips because all listed stages are implemented |
| `UV_CACHE_DIR=/tmp/uv-cache-work016 uv run pytest -q` | passed (0); final run 218 passed, 1 skipped in 3.84s | Full configured offline suite |
| `python -m py_compile src/scientific_network/analysis/analyze.py src/scientific_network/evaluation/components.py src/scientific_network/cli.py src/scientific_network/pipeline.py` | passed (0) | Changed Python modules compile |
| `UV_CACHE_DIR=/tmp/uv-cache-work016 uv run research-network evaluate --help` | passed (0); frame, predictions, gold, config and output arguments displayed | Offline CLI contract check |
| Config hashes | `quality.yaml` SHA-256 `fd37163b6d8cd7302b1b1fcee128b97d8c32f059fd9f4126de37405f2ce65deb`; `analysis.yaml` SHA-256 `46d2d78bb08909c078d6de495f1ccfc843dde5c68bc47efaaf3cdaa9df404e2c` | Configs unchanged; methods `component-evaluation-v1` and `named-projection-analysis-v1` |
| V10 output hash audit | passed; all 42 output hashes match; 98 eligible / 10 no-edition / 22 unresolved / 40 access-unavailable; 94,857 observations (91,355 included / 3,502 excluded); 76,629 assignments / 1,095 tests | `data/manifests/five-year-roster-v10/summary.json` and its 42 outputs |
| `git diff --check` | passed (0) after final code and documentation edits | Worktree whitespace check |
| Markdown local-link scan | passed; 9 updated Markdown files, zero missing local targets | README, project plan, pregraph plan, status, roadmap, evaluation, work-log index/entry, and local Site Report |
| Sites `get_site` | passed; active public version 18, same title, project ID and URL | Read-only state check against prior v18 receipt |
| Supported Sites source helper | failed (128) before checkout; Git host DNS lookup failed | No source audit, build, push, saved version or deployment |

## Decisions

None. Existing scope, methodology and quality thresholds are unchanged.

## Open issues and limitations

No real component labels or evaluation results exist. The synthetic evaluator is
only a protocol check. P01 remains incomplete with 62 candidates; P02 remains
no-go with one reviewer and unknown hours and a second reviewer unconfirmed. The
public Site remains at version 18 because its source helper failed before
checkout; the local Report is not live. No roster, frozen split, enrichment,
graph, database or project Git remote state changed.

## Next step

Resume P01 from roster v10 when the official-source DNS route is available: capture
and hash the next permitted official roster, reconcile track/edition scope, and
update only a new roster version after full checks. Retry the authorized Site
source/publish workflow when its Git host resolves.

## Corrections

None.
