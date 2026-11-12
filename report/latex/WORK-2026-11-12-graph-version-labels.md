# Remove graph version labels from the manuscript

Status: complete. Finalized: 2026-11-12T08:59:47+07:00. Date: 12 November 2026 (Asia/Bangkok, +07:00).
Write scope: `report/latex/` only. All report changes remain uncommitted.

Remove graph version labels, graph-version metadata discussion and the overview
version block from both rendered reports. Keep the same verified graph inputs,
quantitative findings, provenance manifests and material limitations. Preserve
the seven unresolved DOI discrepancies and the distinction between the later
code correction and unchanged collected records. Keep the correct reproduction
link with a descriptive display label. Rebuild, check parity and inspect layout.


## Changes and preservation

Removed visible graph-version labels from the overview, five chapters, schema
explanations, diagram captions and reproduction-link labels in both languages.
Removed the unused graph-version macro. Internal source paths and provenance
manifests still identify the exact frozen graph. Numerical findings, accepted
example edges and material limitations are unchanged. The DOI caveat retains
the seven unresolved discrepancies and explains that the later code correction
did not change the retained records.

## Checks and outcomes

- `make -C report/latex all`: exit 0 on the final build.
- `.venv/bin/python report/latex/scripts/verify-report.py`: exit 0; numerical
  parity, pinned sources, example edges, figures, fonts, references and geometry
  passed. Added a check rejecting graph-version labels in extracted PDF text.
- Both PDFs: 24 portrait A4 pages; no missing glyphs or references, box warnings,
  or visible graph-version labels. Vietnamese accents remain intact.
- Rendered all 48 final pages with `scripts/render-review.py`; inspected all six
  contact sheets and high-resolution English/Vietnamese data pages and the
  Vietnamese pipeline page. No clipping, overlap or sparse spill pages remain.
- The initial expanded DOI caveat produced a sparse extra page in both reports
  and failed the density check. Concise wording preserving all material facts
  fixed the spill; fonts, margins and density checks were not reduced.
- `git diff --check -- report/latex`: passed. Outside-report tracked changes
  match the task-start snapshot. No production data or unrelated code edited.

Evidence: `review/graph-version-label-removal-2026-11-12/`, including final build
and verification logs, focused checks, page images and contact sheets. Current
verification receipt: `review/redesign/verification.json`.

HEAD remains `34e43de`. No staging, commit, push or deployment performed.
Next step: final human proofreading of both PDFs before submission.
