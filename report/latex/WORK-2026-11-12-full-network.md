# Complete network views

Status: complete. Finalized: 2026-11-12T10:23:54+07:00. Scope: report/latex/ only. No graph or analysis changes.

Add a complete heterogeneous graph view to the inventory chapter and a complete
coauthorship view to the collaboration analysis. Every eligible node and accepted
edge will be displayed, with explicit denominators, translated legends, identical
coordinates across languages and pinned input provenance. Preserve the detailed
local neighborhood for a different scale of interpretation.


## Changes

- Added Figure 3.1, the complete heterogeneous graph: all 47,875 nodes and
  225,731 accepted edges, five node colors, ten relationship types. Explained
  why its single connected component differs from the coauthor projection.
- Added Figure 4.3: all 32,189 researchers and 80,482 accepted coauthor pairs,
  all 2,936 components and isolates. Left: entire network; right: enlarged
  largest component (20,776 researchers), using identical coordinates.
- Retained the local neighborhood for names and detailed collaboration support.
- Generated localized figures with shared coordinates and ID/source/layout-hash
  receipts; verifier checks exact full inclusion and cross-language parity.
- Added optional report-local igraph renderer and reproduction guidance; no
  dependency lockfile, graph, source record, analysis result or app changed.
- Removed all reference access-date notes at the user's follow-up request,
  retaining URLs, publication years and descriptive source notes.

## Verification

`make -C report/latex all` and `.venv/bin/python
report/latex/scripts/verify-report.py` passed, exit 0. Both PDFs are 25 portrait
A4 pages (previous edition 24; original baseline 46), with twelve figures each.
No overflow, missing glyphs/references or outside-page text. Pinned source hashes,
accepted example edges, numerical parity and unchanged UET logo pass. Extracted
text has no access-date notes or graph-version labels.

Rendered every final page (50 total), inspected all contact sheets, and rechecked
the changed final Chapter 3 sheets and enlarged graph pages. Inspected pages 12,
13, 16 and 25 individually in both languages at 1700px, including Vietnamese plot
labels, captions and bibliography. Final layout has a dedicated whole-graph page
and an intact quality section; a preliminary split that left a sparse spill page
was corrected without reducing fonts or margins.

The initial layout run was interrupted and restarted with initial coordinates
scaled to graph size for grid acceleration. Final cached layouts rendered both
languages successfully. A first coauthor view made the core too small, so the
final figure adds a separate enlargement of the entire core.

Requested bounded review used GPT-6-Luna at High reasoning effort, read-only in a
fresh context. It confirmed counts/EN-VI parity and identified two presentation
corrections, both resolved (PNG resolution and Vietnamese teal wording).
See `review/full-network-2026-11-12/bounded-review.md`.

`git diff --check -- report/latex` passed. Outside-report source changes remain
byte-identical to the earlier task-start snapshot; pre-existing untracked work
remains untouched. No staging, commit, push or deployment performed.

Artifacts: `build/report-{en,vi}.pdf`, `figures/{en,vi}/full-*`, new renderer,
and `review/full-network-2026-11-12/` (final build/verification logs, complete
page renders/contact sheets and high-resolution details).
Next step: final human proofreading; commit/push only when requested.
