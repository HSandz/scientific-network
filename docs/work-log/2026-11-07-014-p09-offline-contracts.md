# WORK-2026-11-07-014 — P09 edge-audit packet tooling

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 21:13 +07:00; updated 2026-11-07 21:52 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-013](2026-11-07-013-p02-resource-snapshot.md) |
| Git state | main at 66e692d; extensive pre-existing uncommitted work preserved |

## Objective

Advance independent P09 preparation while P01 source capture and P02 capacity
remain blocked. Add standalone offline tools for freezing a hash-bound edge-review
sample and scoring completed double-review packets. Preserve `analyze` and pipeline
`evaluate` as nonzero placeholders until their full contracts exist. Do not claim
release readiness, independent human review, a final edge audit, or semantic
quality from synthetic examples.

## Changes and findings

- Added `freeze-audit-sample` and `score-edge-audit`. The deterministic SHA-256
  rank sampler records a global 600-edge sample and separate per-relation samples
  of 100 or the full smaller type. CSV rows bind graph/config/method/frame and
  readiness-receipt hashes;
  the scorer checks two distinct reviewer IDs per sampled edge, requires a
  reasoned adjudication on disagreements, treats unverifiable outcomes as
  incorrect, and reports global/per-type precision and Wilson intervals.
- Non-synthetic graphs require a matching post-build readiness receipt; its hash
  is included in the sample, review and adjudication packets. The configured
  graph-size/relation gates also apply. Sample and score outputs refuse overwrite.
  Synthetic output is explicitly `synthetic_protocol_only`; reviewer identity and
  independence remain input-declared and unverified. `analyze` and pipeline
  `evaluate` remain placeholders. Component recall/coverage and P09 overall remain
  incomplete.
- Added the separate [adjudication CSV template](../templates/edge-audit-adjudications.csv)
  and documented the command/packet contract in [evaluation.md](../evaluation.md).
  The evaluation package docstring now distinguishes these utilities from the
  incomplete pipeline `evaluate` stage.
- Refreshed the local [Site Report snapshot](../../reports/site-report.md). No
  public Site publication was attempted in this iteration; the user's explicit
  Sites credential authorization covered the audited v10 source operation only.
  The public Site remains v18.
- Rechecked 12 official/Sites source hosts; all failed DNS resolution. A repeated
  `docker system df -v` failed on Docker socket permission. P01/P02 remain blocked
  as documented in WORK-013. V10 is unchanged: 42/42 output hashes verify,
  76,629 assignments and 1,095 protected tests remain intact. No source roster,
  split, enrichment, graph or database data changed.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `UV_CACHE_DIR=/tmp/uv-cache-work014 uv run pytest tests/test_edge_audit.py tests/test_cli.py -q` | passed (0); 12 tests | `tests/test_edge_audit.py`, CLI pending-stage behavior |
| `UV_CACHE_DIR=/tmp/uv-cache-work014 uv run pytest -q` | passed (0); earlier run: 211 tests in 3.72 s | Full configured offline suite |
| `UV_CACHE_DIR=/tmp/uv-cache-work014 uv run research-network freeze-audit-sample --input tests/fixtures/synthetic_graph.json --config configs/quality.yaml --output reports/runs/WORK-2026-11-07-014/synthetic-review-form-v3.csv` | passed (0); synthetic protocol form; no review supplied and no audit performed | Ignored WORK-014 run artifact |
| `UV_CACHE_DIR=/tmp/uv-cache-work014 uv run research-network score-edge-audit --input tests/fixtures/synthetic_graph.json --reviews reports/runs/WORK-2026-11-07-014/synthetic-reviews-v3.csv --config configs/quality.yaml --output reports/runs/WORK-2026-11-07-014/synthetic-audit-v3.json` | passed (0); `synthetic_protocol_only`, `ineligible_synthetic`; invented judgments are not research results | Ignored WORK-014 run artifact |
| Focused test rerun on 2026-11-07 21:43 +07:00: `UV_CACHE_DIR=/tmp/uv-cache-work014 uv run pytest tests/test_edge_audit.py tests/test_cli.py -q` | passed (0); 13 tests | Edge-audit contract and CLI behavior |
| Full test rerun on 2026-11-07 21:44 +07:00: `UV_CACHE_DIR=/tmp/uv-cache-work014 uv run pytest -q` | passed (0); 212 tests in 3.72 s | Full configured offline suite |
| Existing v4 form check: `find`/`stat` and CSV header inspection | passed; output already existed with the expected hash-bound blank-form schema and 27 sample rows; an attempted rerun to that path exited 1 without overwriting it | `reports/runs/WORK-2026-11-07-014/synthetic-review-form-v4.csv` |
| v4 synthetic review packet creation | passed; wrote 54 invented rows (two synthetic reviewer IDs for each of 27 fixture edges); no human review occurred | `reports/runs/WORK-2026-11-07-014/synthetic-reviews-v4.csv` |
| `UV_CACHE_DIR=/tmp/uv-cache-work014 uv run research-network score-edge-audit --input tests/fixtures/synthetic_graph.json --reviews reports/runs/WORK-2026-11-07-014/synthetic-reviews-v4.csv --config configs/quality.yaml --output reports/runs/WORK-2026-11-07-014/synthetic-audit-v4.json` | passed (0); `synthetic_protocol_only`, `ineligible_synthetic`; no release result | `reports/runs/WORK-2026-11-07-014/synthetic-audit-v4.json` |
| Final docs validation on 2026-11-07 21:52 +07:00 | passed; `git diff --check`, trailing-whitespace scan and relative-link check across the five touched Markdown files | Current task docs and README |
| `python -m py_compile src/scientific_network/evaluation/edge_audit.py src/scientific_network/evaluation/__init__.py src/scientific_network/cli.py src/scientific_network/pipeline.py` | passed (0) | Changed Python modules compile |
| v10 summary output hash audit | passed; 42/42 match; edition counts 98/10/22/40, 94,857 observations, 76,629 guarded assignments and 1,095 tests unchanged | `data/manifests/five-year-roster-v10/summary.json` and outputs |
| `git diff --check`, Markdown/CSV whitespace scan and local-link check | passed (0); no whitespace errors and all relative links resolve in ten updated files | Repository diff and current task documentation/templates |
| Sites `get_site` | passed; same project remains active/public at version 18 and the existing URL | Read-only verification; no Site credential, source push or publication used |
| Final source-host DNS probe | failed for all 12 checked hosts; no local source retrieval or roster change | P01 remains blocked |
| `docker system df -v` | failed (1); permission denied on `/var/run/docker.sock` | Docker/database storage remains unmeasured |
| First `uv run pytest ...` without `UV_CACHE_DIR` | failed (2) because the default uv cache is read-only; rerun with `/tmp/uv-cache-work014` passed | Environment restriction; no source changes from failed attempt |
| Initial synthetic CLI score smoke | failed (1) on a missing Wilson interval for synthetic census; fixed and covered by the 212-test suite and successful final smoke run | No result artifact from failed invocation; final output remains protocol-only |
| Repeated `freeze-audit-sample` to the existing v4 output path | failed (1) by design because sample outputs refuse overwrite; the existing form was inspected and retained | No overwrite or mutation |

## Decisions

None. The evaluation packet schema is an implementation contract for future inputs;
it does not alter reviewer requirements or quality thresholds.

## Open issues and limitations

No real review packet or reviewer labels are available. The v4 labels are
invented solely to exercise the synthetic CLI contract. The scorer cannot
establish reviewer identity or independence. P01 source capture remains blocked
by DNS failures; one reviewer is reported with unknown hours and a second is
unconfirmed, so the P02 reviewer capacity is not established. The full `evaluate`
stage, component recall/coverage and final P09 completion remain pending.

## Next step

Continue P01 when official source DNS/access is restored. Keep P02 no-go until the
deduplicated work frame, prospective P03 design, measured batch budget, isolated
database resources, and two reviewers with confirmed hours are available. Finish
the component `evaluate`/`analyze` contracts separately; do not draw a real audit
sample before an authorized final graph.

## Corrections

None.
