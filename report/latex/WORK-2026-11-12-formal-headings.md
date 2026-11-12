# Formal section headings

Status: completed. Recorded: 2026-11-12T08:44:27+07:00 (Asia/Bangkok).
Write scope: `report/latex/` only. Existing report and unrelated identity-quality
changes are preserved. All report changes remain uncommitted as requested.

Replace interrogative and conversational section headings with formal descriptive
headings in both active language editions. Preserve scientific prose, numerical
findings, figures, tables and section order. Rebuild both PDFs, check translated
TOC entries and heading layout, and verify body content has not changed.

## Changes

Changed 11 corresponding section headings in each edition. All five question
headings in the analysis chapter are now descriptive titles covering publication
and topic trends, researcher collaboration, organization collaboration,
community structure and centrality, and within-corpus citations. Also formalized
metadata processing, NLP classification, schema semantics, the graph example,
graph inventory and structural validation headings. Numbering and order remain.
Generated TOC entries update automatically. The preserved original chapters are
historical sources and were not edited.

## Verification and outcome

- `make -C report/latex all`: exit 0; both editions remain 24 portrait A4 pages.
- `.venv/bin/python report/latex/scripts/verify-report.py`: exit 0; numerical
  parity, frozen inputs, figures, example edges, fonts, references and geometry
  pass. Final logs have no warnings or overfull/underfull boxes.
- `scripts/render-review.py`, both editions: exit 0; 48 page images generated
  and all six contact sheets inspected. Both TOCs and the long Vietnamese
  community/centrality heading were inspected at 1800px resolution: pass.
- Source comparison against the saved task baseline confirms that only section
  heading strings changed in the chapters. All scientific prose, figures,
  tables, values and section order are unchanged. No active heading or generated
  TOC entry is a question. Corresponding bilingual titles preserve meaning.
- Outside-report tracked diff is byte-identical to the task-start snapshot.
- `git diff --check -- report/latex`: passed.

Evidence is under `review/formal-headings-2026-11-12/`: saved previous PDFs,
source snapshot, build/verification logs, `heading-checks.json`, full renders,
contact sheets and higher-resolution TOC/heading views. The full verifier
receipt is `review/redesign/verification.json`. No graph, quality artifact,
application or database changed; no repository-wide suite or new analysis ran.
All changes remain uncommitted. Next: final human proofreading and separately
authorized submission.

## Current PDF hashes

- `build/report-en.pdf`: `3ba6f490dd3aef2e6afed26a60ff908dbe9d2719588c27141e66625b9055bdf8`
- `build/report-vi.pdf`: `dc51fb55b3c212b03752eb1c6ebbaac00b0c391bb2c5880795bb9fb2fc15c552`
