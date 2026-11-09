# WORK-2026-11-09-005 — Measured report and local rendering

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09T12:38:08.075848+07:00 (Asia/Bangkok) |
| Work performed | 2026-11-09 +07:00 |
| Contributor | Codex coordinator; renderer implementation by /root/agent_scorer |
| Related task | WORK-2026-11-09-004 |
| Git state | main, evaluation checkpoint `22037a1`; report/renderer changes pending |

## Objective

Complete report/README from measured AI results and validate the local report renderer/package tooling without changing frozen graph artifacts.

## Changes and findings

- Completed report sections/README from actual edge/topic JSON: failed 88% audit and Wilson interval, separate supplements, errors/agreement, coverage/micro/macro topic metrics, source dependence and raw observed-ORCID conflict omission.
- Preserved graph/classifier/test/figures; added a new caption version distinguishing reused computation. Historical pilot/GROBID measurements explicitly dated and separated from release results.
- Added portable HTML/A4 PDF and permitted-source ZIP tooling plus 11 meaningful synthetic regressions; exact reproduction instructions/local delivery checklist and factual agent contributions. Human identity/course facts stay pending.
- Updated roadmap for implemented evaluation and render/package capabilities. No external Site changes; its workflow was read for future authorized delivery.

## Verification

| Check | Outcome | Evidence |
| --- | --- | --- |
| `uv run pytest`; `uv run research-network schema` | 419 passed/1 existing skip; schema exit 0 in WORK-004 with this unchanged renderer code present | WORK-004 run logs |
| `uv run --extra report python -m scientific_network.reporting.release_package --help` | exit 0 | CLI usage checked |
| Same module `--report reports/final-report/report.md --output-dir reports/runs/WORK-2026-11-09-005/report-preview-v1` | exit 0; 19 A4 pages, six figures, 13 H1/H2 headings; local refs present in tracked package; no local-file PDF annotations | ignored preview receipt/manifest/PDF/HTML |
| FontTools cmap on complete rendered text | zero missing DejaVu Sans glyphs; zero extracted replacement glyphs | actual text/embedded fonts checked |
| Raster visual inspection | contact sheet of 16 representative pages including identity/NLP, figures 1–6, all quality tables and code; no clipping/overlap or broken glyphs | ignored `report-preview-v1/contact-sheet.png` |
| `git diff --cached --check` | exit 0 | staged source whitespace check |

Preview package records working-tree bytes before the source checkpoint; final package must be rendered from the ensuing committed snapshot. External report DOI availability was checked in WORK-004; GitHub HTTP504 remains not_verified. No claim of fresh idempotent replay.

## Decisions

Frozen figures/analysis reused; updated captions identify AI-assessed scope. Local package remains a submission draft while personal/course facts are unavailable.

## Open issues and limitations

No human validation or established evaluator independence/course accuracy. No external delivery authorized.

## Next step

Create WORK-006, render/package the committed source snapshot, verify ZIP/member/source/freeze hashes and configured-secret exclusion, then record the final local receipt.

## Corrections

None.
