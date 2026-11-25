# WORK-2026-11-26-001 — Non-report close-out: K1 answer arm, citation labelling, supplementary precision, v4 regressions, hygiene, data release, README

| Field | Value |
| --- | --- |
| Status | completed (two baseline refreshes, publishing and model choice await user decisions) |
| Recorded | 2026-11-26 04:20 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-26 |
| Contributor | Agent execution session (Claude Code, claude-opus-5-5) with the user |
| Related task | [WORK-2026-11-25-006](2026-11-25-006-m4-eval-polish-deploy-prep.md) |
| Git state | `main` from `e572055`; untouched: ~15 line-ending CSVs, user's `docs/README.md`, untracked `docs/prompts/implement-final-exam-track-a.md`; nothing pushed |

## Objective

Close the reviewer's remaining non-report issues (deployment, arXiv report, slides, video and Q&A
sheet out of scope): K1 answer arm, citation labelling, supplementary precision, v4 Explorer
regressions, public-repository hygiene, a local data-release bundle, README and the §9 checklist.

## Changes and findings

1. **K1 answer-quality arm.** The protocol [`configs/k1-answer-v1.yaml`](../../configs/k1-answer-v1.yaml)
   and the runner were committed (`c790eb6`) before any run. It uses the qa-eval-v1 S4 pipeline (RAG
   code byte-identical to `433903d`) and the qa-eval-v1 scorer on the 19 kept development questions,
   uncached, temperature 0, seed 0, thinking off, at 16,384 context. Only the model changes.
   **Development answer accuracy** (15 factual questions, `PYTHONHASHSEED=0`):
   - Qwen3.5-4B 0.502 [0.273, 0.735];
   - Gemma-4-E4B-it 0.469;
   - Qwen3.5-9B 0.634.

   Faithfulness was 19/19, 18/19 and 18/19, and planner JSON first-pass validity 18/18 for all three.
   Decode speed was 79 / 67 / 52 tok/s, and GPU use over idle 3.3 / 3.4 / 5.1 GB.

   The 9B's gain of +0.132 meets the §6.1 10-point margin at all 20 hash seeds (+0.112 to +0.152).
   **No model switch:** that needs the team's decision. Results are in
   [`reports/final-exam/k1-answer/`](../../reports/final-exam/k1-answer/results.md), and a dated
   section was appended to the [K1 report](../../reports/enrichment-v1/k1-model-selection.md) (`3814fd4`).

   Findings along the way:
   - The qa-eval-v1 scorer is hash-seed dependent: `UnifiedEntityResolver.resolve` iterates a `set`.
   - The global map stage truncates JSON at 512 tokens for both Qwen models. The same happened in
     qa-eval-v1, where 41 of 66 map calls failed. This is a product limitation and was left unchanged.
2. **Citation labelling** (`1737192`).
   - New prompts `rag-answer-v4` and `rag-local-answer-v3` point aggregate claims to `[step N]`.
   - `label_answer_evidence` (`evidence-labels-v1`) separates **citations** (a paper row or abstract
     excerpt plus the sentence it supports) from **papers in this result** (per step).
   - The API and SSE carry `citations`, `result_papers` and `evidence_labelling`.
   - The Ask page shows inline step and paper chips and both sections, and the Playwright test was
     extended.
   - Re-caching the 7 demos exposed a verifier bug: in `X (lift: 3.2)` the list-head regex took
     `X (lift` as the entity. Unclosed parentheticals are now dropped. The prompt hint was also
     adjusted so the flagship demo keeps its "k of n papers" counts.
   - After the change the 6 answer demos are faithful, `demo-04` disambiguates, and the inline paper
     IDs in `demo-03` went from 28 to 0.
   - qa-eval-v1 results were not altered. A dated note was added to `results.md`.
3. **Supplementary literature-supported precision** (manifest frozen `dcdfcd8` before judging; results
   `e257a8e`).
   - 120 items (60 S2 and 60 S4 hop-1/2 list items) from the frozen raw outputs, seed 20261126, blinded.
   - Evaluators: A `claude -p` (claude-opus-5-5) and B `codex exec` (gpt-6.2-sol), both fresh and
     outside the repository. C is a separate `codex exec` session on 23 disagreements (Gemini is still
     unauthenticated). The building session did not judge. κ(A, B) = 0.708.
   - **S2 0.433 [0.316, 0.559], S4 0.350 [0.242, 0.476]** (0.542 vs 0.583 excluding "unclear").
   - 14 S4 items had no paper shown, and researcher-ranking items cannot be verified from abstracts.
     These limits are reported in a new section of [`results.md`](../../reports/final-exam/qa-eval-v1/results.md)
     and in the `supplementary_literature_precision` key of `results.json`.
4. **v4 Explorer regressions** (`23606ea`).
   - **Degree 26 vs 22:** not a frontend regression. It appears when the v4 suite reuses a backend on
     :8000 that reads the enriched database (7690). That is what Navigator runs do, and
     `reuseExistingServer: true` lets the v4 suite pick it up. It was reproduced: on 7690 the
     heterogeneous hub has degree 26, `database_verified: false`.
   - The `d7f30ab` (11 Nov) frontend in a temporary worktree behaves identically to HEAD against 7689
     (degree 22).
   - **Baseline layout:** the 11 Nov baselines were captured against the production API through a
     proxy, with no local database ([WORK-2026-11-11-002](2026-11-11-002-explorer-focus-layout.md):
     "API preview drift 108/170 to 110/166"). Local 7689 gives 108/170, so the graph region can never
     match.
   - The `visual` `graph-overview` diff is therefore **not only the header buttons**. It also includes
     that data difference and the 12 Nov sidebar help text (`19f82a1`). Neither baseline was updated:
     this exceeds the approved scope, and the user must decide.
   - On the local layout the hub's own focus label was crowded out by 22 neighbour discs, against the
     spec's focus precedence. The cause is latent code, unchanged since `d7f30ab`. Fix: a second
     placement pass for the focus label only, which may overlap node discs.
   - Both baseline specs now refuse a backend whose `/api/health` is not the verified v4 graph.
5. **Hygiene scan** ([report](../../reports/final-exam/repo-hygiene-2026-11-26.md), `bc1f420`).
   - **No secrets** in history:
     - gitleaks reported 187 hits, all SHA-256 hashes and image tags;
     - 13 secret patterns: 0 hits;
     - the real `.env` password and API key values: 0 occurrences;
     - `.env.example` files hold placeholders only, and `ops/llm/*.env` hold model settings only.
   - **Publication problem:** 50 tracked files contain corpus abstract text, all still in HEAD. The
     v1–v4 audit and topic-label review sheets hold near-full abstracts or excerpts for 19–273 papers
     per file. This is against `docs/source-policy.md`. Remediation options are listed; nothing was
     rewritten.
   - Also found: the graph v3 evidence `excerpt` field holds 14,222 abstract sentences (graph files
     are ignored, so these are not in Git).
6. **Data release** (`c01b9c2`). [`ops/release/build-data-release.py`](../../ops/release/build-data-release.py)
   built `research-trend-navigator-data-v1` into the ignored
   `reports/runs/WORK-2026-11-26-001/data-release/`.
   - Size: 57,519,050 bytes `.tar.gz`, SHA-256 `d89e8a7f0a64846a224ebcb053b629647db4973c36f464ad1426f38b1a5871c5`;
     73 files, 68.5 MB uncompressed; MANIFEST SHA-256 `4776201611711a22…`.
   - Contents: graph v3 (50,144 nodes, 242,048 edges) with the 14,222 evidence excerpts and 6
     abstract-quoting generated descriptions replaced by SHA-256; E1 source manifest, entities,
     linking, co-occurrence; E4 v1–v3 quality; analysis-v2; benchmark questions, references and
     receipts; qa-eval-v1 and K1 results; GraphRAG reports and descriptions; README, LICENSES.md,
     MANIFEST.json.
   - Self-check: 0 verbatim 10-word abstract windows over 250,055 indexed windows.
   - Exclusions and reasons are in the bundle README.
   - The licence for project-authored data is recorded as "pending team decision", because the
     repository has no LICENSE.
7. **README, checklist and traceability** (`5cb68b5`).
   - README: Navigator section, results with caveats, quick start, "pending" links for the system
     URL, arXiv and data release, and the AI-assessed statement. The v4 sections are kept.
   - §9: E1–E4, S1–S3 and K1–K3 are ticked with evidence links. Product (not deployed) and P1–P4
     stay unticked with notes.
   - Requirements: the traceability table points to §9.

**Command awaiting approval (not run).** Push `main` first, so the release tag can point at a
published commit; then run:

```bash
gh release create data-v1 \
  reports/runs/WORK-2026-11-26-001/data-release/research-trend-navigator-data-v1.tar.gz \
  reports/runs/WORK-2026-11-26-001/data-release/research-trend-navigator-data-v1/MANIFEST.json \
  --repo HSandz/scientific-network --target main --draft \
  --title "Research Trend Navigator data release v1" \
  --notes-file reports/runs/WORK-2026-11-26-001/data-release/research-trend-navigator-data-v1/README.md
```

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Orientation: `git status`, `git log`, `docker ps`, graph and references SHA-256 | passed; graph `37ee8c59…`, references `d2fcf2c0…`; port 8080 occupied by an unrelated `bifrost` container, so the model ran on `LLM_PORT=8081` | — |
| `python -m scientific_network.evaluation.k1_answer run` ×3 (4B, Gemma, 9B; one server at a time on 8081, `neo4j-enriched` 7690) | exit 0 each; 19/19 status ok each | `reports/final-exam/k1-answer/raw-*.jsonl`, `run-meta-*.json` |
| `PYTHONHASHSEED=0 … k1_answer score` and `scorer_sensitivity run --target k1 --seeds 0-19` | exit 0; outcome above | `reports/final-exam/k1-answer/results.{json,md}`, `hashseed-sensitivity.json` |
| `scorer_sensitivity run --target qa-eval-v1 --seeds 0-19` (frozen raw outputs re-scored in an ignored scratch dir; frozen `factual-scores.json` hash unchanged `ca8735fc…`) | see the dated note in qa-eval-v1 `results.md` | `reports/runs/WORK-2026-11-26-001/qa-hashseed/` |
| `dev_eval --demos-only --llm-base-url :8081` (3 iterations; final) | exit 0; 6/6 answer demos faithful, `demo-04` disambiguation | `reports/final-exam/rag-v1/demo-cache.json` |
| `supplementary_precision sample / judge / aggregate` | exit 0; 120 items, A/B 10 batches each (1 attempt), C 2 batches | `reports/final-exam/qa-eval-v1/supplementary-precision*.json` |
| gitleaks (Docker) on full history + pattern grep + `.env` value check + abstract-window scan | 187 false positives; 0 secrets; 50 files with abstract text | `reports/final-exam/repo-hygiene-2026-11-26.md` |
| `ops/release/build-data-release.py --out-dir reports/runs/WORK-2026-11-26-001/data-release` | exit 0 (first build failed its own abstract self-check on 6 descriptions; fixed); 0 abstract windows | ignored bundle, receipt JSON |
| `uv run pytest -q` | exit 0; 788 passed, 2 skipped (one needs 7690, which was down; `tests/test_rag_tools.py` rerun with 7690: 2 passed) | — |
| `EXPLORER_NEO4J_URI=bolt://127.0.0.1:7689 uv run pytest -q apps/research-explorer/backend/tests` | exit 0; 36 passed | live Bolt 7689 |
| `npm --prefix apps/research-explorer/frontend run build` | exit 0 | — |
| Navigator Playwright on 7690 (`EXPLORER_NEO4J_URI=bolt://127.0.0.1:7690`) | exit 0; 10 passed; routes trends 108 ms, groups 702 ms, communities 75 ms, network 103 ms | `reports/runs/WORK-2026-11-26-001/navigator/` |
| Contracts Playwright | exit 0; 8 passed | — |
| v4 Playwright on 7689 (`dashboard`, `explorer`, `analytics-layout`, `focus-labels`, `reproducibility`, `visual`; `sn-llm` stopped) | exit 1; **44 passed, 2 failed**: only the two screenshot comparisons (`focus-labels` heterogeneous hover 2% diff, `visual` graph-overview 3% diff) against the production-derived baselines; all label, adjacency and geometry assertions pass. A separate first `focus-labels` run failed `researchers` once on a cold backend (5 s poll); it passed warm and in the full suite | `reports/runs/WORK-2026-11-26-001/v4/v4-suite.log` |

## Decisions

[D042 amendment, 2026-11-26](../decisions.md#d042-amendment--k1-answer-arm-citation-labelling-post-hoc-literature-check-release-redaction-2026-11-26).

## Open issues and limitations

User decisions needed:

- whether to accept the 9B (9.65B) as the "9B" model, as §6.1 allows (requires a D042 amendment);
- whether to refresh the two v4 baselines from local 7689 data, or keep them and test against
  production as on 11 November;
- abstract text in 50 public files: keep and disclose, remove going forward, or purge history;
- publishing the data release, and a licence for project-authored data.

Known limitations:

- The global map stage truncates JSON at 512 tokens.
- Evaluator C shares B's model family.
- The supplementary check is post hoc and AI-assessed.
- Deployment, the arXiv report, slides, the video and the Q&A sheet are not done (out of scope).

## Next step

The user answers the four decisions above. Then M5 (arXiv report, due 15 December) starts from
`docs/final-exam/specification.md` §7.

## Corrections

None.
