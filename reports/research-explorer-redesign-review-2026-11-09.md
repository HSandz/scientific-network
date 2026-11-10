# Research Explorer redesign review — 9 November 2026

Review only, using **design-taste-frontend** and its app-screen rules. Compared
with [the original review](research-explorer-design-review-2026-11-09.md).
Reviewed the running development app at `:5173`, a freshly built production
preview at `:4173`, and read-only responses from the API at `:8000`.
No application, dependency, graph, database or public Site changes were made.

## Assessment

The redesign is substantially calmer and more coherent. Keep this visual direction.
The neutral dark surfaces, legible secondary text, compact navigation and contextual
inspector solve much of the original overload. Both themes now look intentional.
The remaining work is primarily graph readability, responsive composition and
interaction reliability, with a separate correction needed to displayed quality facts.

The product's central job remains: find an entity, understand its relationships,
then trace the supporting evidence. The graph is now the biggest thing on screen,
but it still does not make those relationships easy to understand.

## Improvements verified

| Area | Original | Redesigned app observed now |
| --- | --- | --- |
| Desktop graph workspace, 1440px | Main region 736px wide with both rails open | 1168px before selection; 272px filters; inspector initially absent |
| Tablet/phone | Main region 64px / 0px | Full-width workspace at 768px / 390px; panels open as overlays |
| Dark appearance | Blue-slate surfaces, low-contrast labels, tiny metadata | Neutral charcoal, quieter separation, readable selection/hover labels; production inspector reports no failures |
| Graph labels | Heavy label collisions and overlays | Fewer, truncated labels; title, controls and key outside the plot |
| Analytics | Graph rails permanently narrow the charts | Wide overview when details are closed, divided inventory strip, separate quality panel and legends above plots |
| Entity entry | Raw ID inputs | Searchable name selectors with IDs retained as metadata |
| Table consistency | Warut row showed 0 DB edges versus inspector 58 | Both now display 58 DB incident edges |

## Remaining findings, ordered by priority

### 1. High — quality facts and targets disagree

Analytics displays **37,199 / 50,466 authorship positions** for affiliation coverage.
The Caveats dialog and current `reports/release-v4/graph-summary.json` use
**48,259 / 65,469**. Both show 73.71%, but these are different populations; the
Analytics counts do not represent the current release summary.

The same panel states **90% topic coverage and 0.80 micro-F1 targets**. The release
quality config sets topic coverage at **80%** and topic-label precision at **95%**;
the API also reports the latter precision target. Do not invent a replacement F1
gate. Keep the failed topic precision and historical F1 disclosures, while showing
the actual configured targets separately.

Recommendation: render counts, percentages, definitions and targets from shared
versioned evidence/configuration instead of hand-written copies. This is a display
correction; it requires no graph rebuild or threshold changes.

Anchors: `apps/research-explorer/frontend/src/components/analytics/AnalyticsView.tsx:429–452`,
`apps/research-explorer/backend/services/explorer_service.py:99,174–182`,
`configs/quality-release-v1.yaml:35–43`. Evidence: Analytics and Caveats captures,
`settled-review.json`, and the current graph summary.

### 2. High — graph relationships remain difficult to read

The default researcher view reports **100 nodes and 90 edges**, yet looks like a
ring of colored beads with several overlapping clusters. Connections are barely
perceptible. Citation pairs also sit so close that edges and their direction are
hard to distinguish. Organization mode shows the opposite problem: a dense mesh
of 1,119 edges. The heterogeneous view communicates structure more successfully.

Selecting Warut or the sample relationship does not resolve the overlap: connected
nodes can visually collapse beneath each other, even while the inspector correctly
reports seven displayed edges. This is a visual finding, not proof that edges are
absent from the renderer. Label collision management improved; node separation
and relationship legibility still need attention.

Recommendation: tune the display layout and node sizing together, ensure connected
nodes have enough screen separation, and make selection reveal a readable local
neighborhood. Offer a clear action to inspect a cluster. Preserve all underlying
IDs, weights and graph semantics. Community colors are legitimate categorical data,
but cycling 12 hues plus raw IDs still demands too much decoding; emphasize the
selected community and disclose the full key on demand.

Anchors: `components/graph/SigmaGraphCanvas.tsx:266–318,439–500` under the frontend;
backend display layout at `services/explorer_service.py:444`. Screenshots:
`graph-1440-dark`, `graph-390-dark`, `inspector-node-1440-dark`,
`inspector-edge-1440-dark`, `citations-1440-dark`, `organizations-1440-dark`.

### 3. High — mobile and intermediate widths still spend too much space on controls

At **390×844**, the header is 135px tall. The plot starts at **y=360.5px** and is
only **302.3px high, 35.8% of the viewport**. The lower key and quick-selection area
consume another ~181px. The phone can now render the app, but its main task still
gets a minority of the screen. Header controls measure 28–34px high, below the
skill's 44px touch-target recommendation.

At **1024px**, selecting an entity keeps both desktop rails open: 272px filters +
392px details leave a **360px graph workspace**. At 1100px it is only 436px.
The drawer breakpoint is too early for a three-pane workspace. Resizing an open
desktop sidebar to 768px also leaves an overlay open over the graph.

Analytics on a fresh phone view places its first chart panel around **y=1190px**,
after four vertically stacked inventory cells and the quality panel. At 768px the
three quality columns force short metrics into several lines. The phone table
retains an ~820px table inside a 340px frame; its identity column is not sticky,
so scrolling toward scores/actions loses the entity name.

Recommendation: give phones one compact navigation row and one graph-control row;
move secondary tools and layout options into sheets. Collapse the long legend.
Base rail behavior on remaining workspace width. Compact inventory totals into
label/value rows, keep quality limits visible in a concise summary with details,
and make the table a two-line list or keep its identity column fixed.

Anchors: `components/layout/TopHeader.tsx:156–375`,
`components/filters/LeftSidebar.tsx:203–214`,
`components/inspector/RightInspector.tsx:137–147`,
`styles/index.css:186–218`, `components/table/TableView.tsx:362–366`.
Measurements: `focused-review.json`; images: `selected-1024.png`, phone graph,
Analytics and table captures.

### 4. High — keyboard focus does not follow the visible task

Reproduction: focus **Paths**, press Enter, then Tab. Focus remains on the Paths
opener when the dialog opens; Tab moves to **Compare behind the overlay**.
The dialog has neither `role="dialog"` nor `aria-modal`, and focus is not contained.
Closing after using a picker leaves focus on the document body. In the entity
picker, typing `Warut`, ArrowDown, Enter leaves the original Bo An selection intact;
the search input stays open. Escape closes modals, but does not close the filter drawer.

Recommendation: move focus into a labelled dialog, contain it, make background
controls inert while modal, restore focus to the opener, and handle Escape for the
topmost overlay. Implement the entity picker with appropriate accessible semantics
and predictable keyboard selection. Verify the whole search → selection → evidence
sequence with keyboard input.

Anchors: `App.tsx:47–89`, `components/modals/PathFinderModal.tsx:59–68`,
`components/modals/EntityPicker.tsx:125–227`. Reproduction results in
`focused-review.json`. This was a focused keyboard check, not a full accessibility audit.

### 5. Medium — ordinary name searches can miss visible researchers

`Tuomas Sandholm` returns no results (HTTP 200), while `Sandholm` returns the stored
name `Tüomas Sandholm`. This makes the new name-based workflow unnecessarily fragile.
`Warut Suksompong` succeeds. Recommend accent-tolerant retrieval and clear search
guidance, preserving stable IDs and keeping retrieval separate from identity merging.
Never merge researchers because normalized names match.

Anchor: `backend/repositories/neo4j_repo.py:360–400`; API checks in
`focused-review.json`. This review does not establish which source spelling is authoritative.

### 6. Medium — the running development app differs from the fresh build

Fresh browser contexts reproduce stark white rules and outlined controls at
`:5173`, versus subtle borders, filled surfaces and selected navigation at `:4173`.
The header border measures `rgb(229,231,235)` in development and `rgb(41,41,41)` in
production; the development header background is transparent rather than `rgb(23,23,23)`.
The dev inspector also reports an unloaded JetBrains Mono declaration, while the
production inspection does not. This explains why the local app can still look
harsher than the redesigned preview. Cause not established; a stale dev CSS/config
process is a hypothesis. Verify development/build parity before further visual judgment.
No server was restarted during this review.

Evidence: `fresh-5173.png`, `fresh-4173.png`, inspector reports and `focused-review.json`.

## Next iteration

Correct the displayed quality facts first. Then spend the design effort on readable
network relationships and a compact responsive shell. Complete keyboard behavior
before considering the redesign finished. Keep the neutral palette, evidence links,
explicit scopes and AI-assessed limitations. A second wholesale visual restyle is
unlikely to provide as much benefit.

## Screenshot critique and checks

```text
ROUND 1 — redesigned app, review only
Seen in one second: a quiet research workspace around a large colored-node plot.
Idea: research connections become an evidence-linked workbench.
Live task: find an entity, examine its neighborhood, trace supporting papers.
Layout: compact shell / broad graph / ledger table / divided totals and chart grid / contextual evidence pane.
Scores: design 7 · usability 5 · creativity 6 · content 6 → overall 6.1/10 (previous 4.9).
Usability held at 5 for graph overlap, cramped intermediate widths and keyboard failures.
App exemptions apply: legitimate borders, technical monospace and semantic category hues.
No picture or motion floor; no new direction draw or implementation fixes.
```

Scores are subjective, not scientific accuracy measurements. The content score
reflects useful evidence access alongside the verified conflicting display facts.

- Fresh production build: **pass**, with Vite's >500kB chunk warning (1.54MB raw
  JavaScript, 476kB gzip). Performance was not benchmarked.
- Skill browser inspector: production **0 FAIL, 0 WARN**; development **0 FAIL,
  2 WARN** (development server and declared/unloaded mono font). These results
  concern the default Graph screen at three widths, not every interaction or panel.
- Skill source lint: **0 FAIL, 36 WARN**, all monospace occurrences. IDs, hashes
  and code have legitimate uses under app rules; warnings are not 36 functional bugs.
- Existing Chromium E2E suite against `:4173`: **4 passed**. Supplemental capture
  run produced 22 screenshots with **no console or uncaught page errors**. All
  22 captures and the inspector fold/contact sheets at three widths were opened;
  targeted responsive, keyboard and lower-chart captures were also reviewed.
- Both themes reviewed on desktop and phone; light preference survives reload.
  An immediate theme-transition screenshot was retaken after settling and is not
  treated as a persistent color defect.
- Baseline `uv sync --locked --group dev --extra analysis --extra report`: **pass**;
  `uv run pytest`: **508 passed, 1 existing skip**, exit 0. `git diff --check`: pass.
- Tracked app/dependency diff compared byte-for-byte with the initial snapshot:
  unchanged. Prior staged and unstaged work preserved. Only this report and work
  records were changed. No commit, graph rebuild, publication or deployment.
- Raw captures, measurements, scripts and logs are ignored under
  `reports/runs/WORK-2026-11-09-019/`. This is a local Chromium design/usability
  review, not cross-browser certification or a new semantic/scientific audit.
