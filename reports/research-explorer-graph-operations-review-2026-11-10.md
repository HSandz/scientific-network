# Research Explorer — graph operations review

10 November 2026; `main` at `41852c6`; review only using
`design-taste-frontend` app-screen rules. Extends the
[website review](research-explorer-improvements-review-2026-11-10.md).
Implementation handoff: [combined plan](../docs/research-explorer-graph-usability-plan.md).

## Overall assessment

The graphs offer useful data and evidence access, but several operations currently
change or misrepresent the view in ways their controls do not explain. Keep the
soft graphite design and improve the interaction/state model before further
visual decoration. The hover-label complaint is reproduced, not a preference
inferred from screenshots.

## Hover and readability across all four projections

Real pointer hovers were combined with read-only inspection of Sigma's rendered
graph and canvas text draws. These are observations of the selected examples at
1440×900, not averages across all nodes. “Named” below includes truncated names.

| Projection / hovered entity | Canvas nodes / edges | Visible neighbors | Neighbor names drawn |
| --- | --- | --- | --- |
| Researchers / Warut Suksompong | 100 / 90 | 7 | 1 |
| Organizations / Zhejiang University | 60 / 1,119 | 53 | 10 |
| Citations / Informer | 80 / 43 | 2 | 2 |
| Knowledge graph / Representation learning | 113 / 177 | 28 | 1 |

The code forces only the center label (`SigmaGraphCanvas.tsx:496–505`). Neighbors
remain subject to the overview's spatial grid and collision suppression. This
makes highlighting much less informative: users can see that relationships exist
but cannot identify most endpoints. The simple citation example fares better;
its long paper titles are still truncated. The organization overview is very dense,
and knowledge-graph edges are hard to distinguish by predicate without inspection.

## Confirmed functional findings

| ID / priority | Reproduction and impact | Source / direction for correction |
| --- | --- | --- |
| G01 High usability | Hover Warut: 7 neighbors highlighted, 1 neighbor name drawn. Topic: 28 neighbors, 1 name. Repeatedly moving between nodes changes the focus being examined. | Separate overview and focus label policies; add a complete named, selectable list of visible neighbors and pinning. |
| G02 High | Ego view returns a 59-node / 184-edge neighborhood but the canvas becomes 151 nodes / 263 advertised edges. It retains unrelated base nodes instead of isolating the neighborhood. | `App.tsx:190–225` always merges the base, even when store `mergeSubgraph(..., true)` was used. Introduce explicit replace vs append view state and Back. |
| G03 High | Expanding from Researchers adds Paper/Organization nodes and AUTHORED/AFFILIATED_WITH/CITES edges while the title/key still describe COAUTHORED_WITH researcher collaboration. Mode/sector/support constraints are not forwarded; only years and a limit are sent. | `App.tsx:227–245`. Stay within the current projection by default; an all-relations exploration must be an explicit, correctly titled switch. |
| G04 High | Expanded/Ego canvas advertises 263 edges, but Sigma contains 261. Two reciprocal CITES edges are dropped. The current four unexpanded examples retain their edges; loss was reproduced after expansion. | `SigmaGraphCanvas.tsx:297,335–337`: non-multi graph plus an unordered endpoint-pair duplicate check suppresses valid edges. Preserve every edge ID and direction, with separate lanes for parallel/reciprocal relationships. |
| G05 High | Expanded Warut has 58 rendered incident edges; inspector still says “7 visible edges.” Under Strong links, actual degree is 6, inspector says 7. Counts/strength are stale payload metrics. | `RightInspector.tsx:369–375` reads base node values; derive visible metrics from the final rendered slice. Preserve separate full-projection metrics. |
| G06 Medium | Select Warut, then Circle/Radial: details remain Warut but selection highlighting disappears. Switch to Organizations: Warut remains selected off-canvas, so every organization is dimmed. | Renderer is recreated without reapplying unchanged selection reducers; `setViewMode` leaves selection/hover intact. Define selection behavior across layout and projection changes. |
| G07 Medium | Zoom in, then Expand: camera ratio resets from 0.667 to 1. New nodes use separate layout coordinates and produce a broad fan across the old graph. Circle/Radial create overlapping node rings at the reviewed count. | Preserve renderer/camera/positions where possible; place additions locally. Treat layout algorithms as presentation, not community evidence. |
| G08 Medium | Strong links on Citations leaves all 43 edges visible. Researchers filter shows 54 edges, but downloaded JSON contains 90. Shared URL reload returns 90 edges and loses the filter. | Empty-filter fallback, export uses prefilter props, and URL omits local filter/layout plus most scope settings. Use a single effective-view definition. |
| G09 Medium | “Visualize path” adds a 3-node / 2-edge result to the researcher overview: 102 nodes / 92 edges, no dedicated path emphasis, and a researcher-only key despite the organization endpoint. | `PathFinderModal.tsx:222–233` plus base merge. Open an explicit path view with ordered steps, labels, direction and Back to previous view. |
| G10 Medium | Simulated 503 on neighborhood retrieval: spinner ends, graph remains unchanged, and no failure/retry message appears. Error is logged only to console. | `App.tsx:239–240`. Show an inline operation error and Retry while keeping the last valid graph. |
| G11 Medium | At 390px, layout and edge visibility controls are hidden and absent from the tools menu. Phone Researchers collide; Organization and knowledge-graph views are crowded. | `SigmaGraphCanvas.tsx:735–770`, header mobile menu. Provide reachable tools, touch selection/pinning and a usable neighbor sheet. |

The inspector's global connection groups also show relations outside the current
canvas and only a bounded item list. They are useful but are not a substitute for
a list explicitly aligned with the highlighted, currently visible neighborhood.

## What works in the exercised flows

- All four default projections load. Initial runtime edge totals agree with their
  respective captured API payloads: 90, 1,119, 43 and 177 edges.
- Node pointer hover highlights incident connections. Node selection opens details.
- A direct pointer click on a canvas edge opens evidence. The settled sample
  correctly identifies COAUTHORED_WITH as a symmetric derived relation and lists
  eight supporting papers with source links.
- Citation arrows in the reviewed simple example point toward the cited paper.
  This does not excuse reciprocal-edge loss after expansion.
- Node dragging changes display coordinates without accidentally selecting that
  node in the tested drag. Zoom works until graph recreation resets it.
- Soft dark mode and light mode retain consistent visual identity. Readability
  problems persist in both; another palette rewrite would not solve them.

## Proposed interaction principle

Keep overview labels sparse. On hover, identify the center and its immediate
neighbors together; on click/tap, pin that neighborhood and expose a stable list
of all visible neighbor names. For dense neighborhoods, show the labels that fit
and put every remaining name in the list with an explicit count. Do not silently
suppress names or print 53 overlapping labels. A focused view can spread the
neighborhood; Back restores the previous overview and camera.

## Verification, evidence and limits

Fresh checks in this task:

- `uv sync --locked --group dev --extra analysis --extra report`: exit 0.
- `uv run pytest`: **508 passed, 1 existing skip**, exit 0, 20.72s.
- `node reports/runs/WORK-2026-11-10-003/graph-review.mjs`: final run completed
  all four projections, hover/selection, layouts, expansion/Ego, mode switch,
  filter and phone checks; no page exceptions recorded.
- `node .../supplemental-review.mjs`: completed Paths, JSON download/share reload,
  simulated expansion error and drag checks.
- `node .../final-checks.mjs`: completed settled evidence, actual canvas-edge
  pointer click, filtered degree, and eight light screenshots (all projections
  at 1440 and 390px); screenshots/contact sheets inspected.
- Runtime diagnostics read Sigma refs and collect canvas text calls in the test
  browser. No application files or database records were changed. An initial
  timing/selector issue in the harness was corrected before the completed runs;
  stale React-fiber prop snapshots are not used as API-count evidence. Captured
  API responses and runtime graphs establish the initial totals above.

Raw scripts, captures and JSON are ignored under
`reports/runs/WORK-2026-11-10-003/`. Main summaries: `hover-summary.json`,
`graph-review.json`, `supplemental-review.json`, `final-checks.json`.

WORK-002's 14 backend tests, 4 E2E, build and skill inspector results are historical
from the preceding review of the same application commit; they were not rerun
here. This is not a fresh scientific accuracy audit, an exhaustive check of every
node/preset, or device-level touch/screen-reader certification. No graph semantics,
frozen data, public Site, release package or application code changed.

Clarification to WORK-002's sizing source pointer: the active renderer computes
size inline at `SigmaGraphCanvas.tsx:316–317`; the exported `getNodeRadius` helper
cited in that review is not called by this canvas. The observed phone collision
finding remains valid. This dated clarification preserves the earlier record.
