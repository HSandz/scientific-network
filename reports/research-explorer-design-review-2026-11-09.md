# Research Explorer design review — 9 November 2026

Review only. No frontend, backend, graph, dependency-file or deployment changes.
Method: design-taste-frontend, using its app-screen rules and screenshot critique.
Reviewed the existing Vite app at `http://127.0.0.1:5173`; port 8000 serves its API
(the API root returns 404). This is a development-server review, not production QA.

## Assessment

The interface contains useful research tools, but too many of them demand attention
at once. Layout and information hierarchy need the largest change. Recoloring the
current interface would leave the crowded header, obstructed graph and narrow
analytics intact.

The intended primary job is: find a researcher, organization or paper, understand
its connections, then inspect the supporting evidence. That sequence should determine
the hierarchy. The graph, entity names and evidence are the product's identity;
decorative dashboard styling adds little.

Keep the working graph/table/analytics views, global search, bounded exploration,
entity comparison, source links, evidence classes and explicit metric scope. Keep
all scientific limitations, including AI-assessed status, human-validation limits
and failed coverage/topic targets. Improve their placement and readability.

## Findings, ordered by impact

| Priority | Finding and observed evidence | Recommended change |
| --- | --- | --- |
| Critical | Responsive layout fails. Both fixed sidebars remain open: 320px filters plus 384px inspector. The main region measures 736px at 1440px, 64px at 768px, and 0px at 390px. Tablet/phone screenshots show clipped controls and almost no graph. | Fold panels into drawers at tablet widths; show one region at a time on phones. Selecting an entity opens its detail sheet, with an obvious return to the graph. |
| High | The empty inspector occupies 384px before anything is selected. Four projection cards, numerous header controls and two bottom overlays surround the graph. Even the product name truncates at desktop width. | Start with the inspector closed. Use a compact projection selector, one clear search entry and a tools menu. Give the graph a stable title/toolbar outside its plotting area. |
| High | Dark-mode legibility is inconsistent. The inspector measures several section labels and Reset at 3.8:1, below its 4.5:1 floor, and finds 21 text blocks below 11px. The selected-node/edge screenshots show pale hover backgrounds with near-white label text. Bright native slider tracks and blue-slate surfaces further compete with the data. | Establish shared dark tokens for CSS, Sigma and ECharts, including hover-label backgrounds and text. Use neutral charcoal surfaces, readable secondary text, subdued control tracks and explicit native color-scheme support. |
| High | The graph is visually congested. Labels overlap around researcher clusters; organization labels collide heavily; long citation titles extend beyond the canvas. Floating title, toolbar, entity strip and legend cover usable graph space. | Reserve a plotting rectangle, suppress colliding labels, prioritize selection/hover and a small ranked label set, and place full paper titles in the inspector. Preserve keyboard-accessible selection when replacing the quick strip. |
| High | Analytics inherits the graph's sidebars. Six KPI cards sit in approximately 106px-wide columns, forcing labels and methodological notes into many lines. Two narrow charts follow; the annual chart legend overlaps its baseline/year labels. The expanded screenshot is substantially clearer. | Give Analytics its own wide content area. Use a compact inventory strip, a separate readable quality section, and charts sized from their container width. Reserve legend space explicitly. |
| Medium | The evidence inspector has substantial content but nests boxes, badges and small metadata throughout. Four actions precede the metrics. Full-projection and displayed values are carefully distinguished, yet hard to scan. | Lead with the entity/relationship and its main supported fact. Use Overview, Connections and Evidence sections or tabs; disclose raw IDs, hashes and method metadata below the evidence summary. Preserve access to every source. |
| Medium | Color carries competing meanings: emerald navigation and actions, teal tools, sky evidence links, amber quality warnings and many community hues. Community colors are hashed into ten repeating colors, while the legend shows six generic “Group” entries rather than actual community IDs. | Quiet the chrome. Retain meaningful categorical encodings and text labels, but make legends describe actual visible categories. Use neutral context plus one focused community when that answers the question. Never imply that equal color proves community identity. |
| Medium | The inventory table keeps graph-only filters beside its own separate filters. Repeated filled “Focus in Graph” buttons are louder than many cell values. Tiny IDs and uppercase headers add noise. | Make scope explicit for each view, use sentence-case headers and consistent numeric alignment, and make the primary row identity easy to read. Use one quiet trailing row action. |
| Medium | Path and Compare ask for raw internal entity IDs. The preset chips help demonstrations, but normal users must know or copy technical identifiers. | Reuse entity search as a name-based picker, retaining the stable ID underneath and in advanced details. |

Source anchors: `frontend/src/App.tsx` (shared shell),
`components/filters/LeftSidebar.tsx:159`, `components/inspector/RightInspector.tsx:85`,
`components/layout/TopHeader.tsx:131`, `components/graph/SigmaGraphCanvas.tsx:190`,
`components/analytics/AnalyticsView.tsx:309`, and `lib/colors.ts:117`, all under
`apps/research-explorer/`.

One additional display-consistency concern needs a separate functional trace:
the table shows Warut Suksompong with “0 edges” while the selected inspector
shows 58 total DB incident edges and 7 displayed-subgraph edges. These could be
different metric definitions or missing values rendered as zero. The UI needs
an unambiguous label or a missing-value marker; this review does not diagnose
the backend cause or change the data.

## Three changes with the largest benefit

1. **Recompose the workspace.** Keep product, search and Graph/Table/Analytics in
   the header; move secondary tools into a menu. Replace the four large mode
   cards with a compact selector: Researchers, Organizations, Citations, Knowledge
   graph. Put weighting, node limits, schema predicates and layout parameters
   under advanced controls. Keep the inspector conditional. Analytics should
   open wide, with the full-graph scope stated next to its title.
2. **Make dark mode a complete design system.** A proposed starting palette is
   ground `#101010`, panel `#181818`, raised `#242424`, text `#eeeeee`, secondary
   `#b7b7b7`, metadata `#969696`, accent `#61bfa5`. These are recommendations,
   not implemented or browser-validated tokens. Map graph labels, hover panels,
   chart axes/tooltips and form controls to the same roles. Use 14px working text,
   12px metadata, 16px section titles and a 20–24px view title. Keep IDs monospace;
   use tabular figures for comparable values. Persist theme choice and support
   the system preference. The skill's preference for neutral darks is an art
   direction rule; the measured contrast failures are a separate issue.
3. **Make relationships easier to read.** Establish a graph plotting area clear
   of explanatory panels; use selection, labels and muted context to guide the eye.
   Keep a compact encoding key, with details available on demand. In Analytics,
   replace cramped KPI tiles with readable summaries and fix chart label/legend
   collisions. Show quality limitations next to the results they qualify and
   retain a clear Data quality entry; do not bury limitations in advanced settings.

The proposed direction is a quiet research workbench with evidence available at
the point of inspection. No direction was dealt: the skill's review workflow
stops after recording and critiquing the existing app. No redesign seed, sample
data, imagery, animation or new dependency is needed for this review.

## Screenshot critique

```text
ROUND 1 — existing app, no fixes
Seen in one second: a crowded control shell around colored graph nodes.
Idea (one sentence): explore the release's research connections and trace their evidence.
Live thing: entity search, graph selection and evidence inspection.
Layout words by section: shell=three panes / graph=overlaid canvas / table=dense rows / analytics=KPI strip and chart grid / evidence=nested detail panels.
Scores: design 5 · usability 3 · creativity 6 · content 8 → overall 4.9
Caps applied: inspector failures cap overall at 6; visibly clipped phone content caps usability at 5. App exemptions apply to picture counts, motion floors, legitimate borders and numeric monospace.
Top three problems (most visible first), each with the screenshot it shows in and the fix:
1. graph-768.png and graph-390.png: sidebars consume the workspace; use responsive drawers and one active pane.
2. graph-dark.png and analytics-dark.png: simultaneous controls and oversized permanent rails compete with the work; simplify the shell and open details contextually.
3. graph-selected.png and before/desktop-fold.jpg: dark hover labels and tiny/low-contrast metadata are difficult to read; unify rendering tokens and lift working type/contrast.
```

These are subjective design scores, not a scientific accuracy assessment. Content
scores reflect specificity and access to evidence; scientific calculations and
the completeness of every disclosure were not independently audited here.

## Verification and evidence

- `inspect.mjs --app http://127.0.0.1:5173 --out reports/runs/WORK-2026-11-09-017/before`
  exited 1: **4 FAIL categories, 3 WARN categories**, across 1440, 768 and 390px.
  All six generated fold/contact-sheet images were opened.
- `lint.mjs --app apps/research-explorer/frontend/src` exited 1:
  **13 FAIL occurrences, 131 WARN occurrences** across 17 source files.
  Counts include house-style preferences; they are not counts of functional bugs.
  Numeric monospace is permitted by app-screen rules, and real dialogs may have
  shadows; those warnings do not warrant mechanical removal. Five categorical
  entity hues can be necessary for this graph; distinguish semantic encoding
  from decorative rainbow charts. The automatic tabular warning needs font-level
  verification because many figures already use a monospace stack.
- Supplemental Playwright screenshots covered all four graph modes, selected node
  and edge, Table, Analytics in both themes, expanded Analytics, lower Analytics,
  Search, Paths, Compare and quality disclosures. Every captured image was opened.
  Width measurements are in `browser-measurements.json`; its run recorded no
  uncaught page errors. Modal layouts were reviewed, not exhaustively function-tested.
- Required baseline: `uv sync --locked --group dev --extra analysis` exited 0;
  `uv run pytest` exited 0 with **502 passed, 7 skipped**. Sync removed the installed
  optional Markdown package, causing six report-test skips. Restored the existing
  report extra with `uv sync --locked --group dev --extra analysis --extra report`;
  repeated `uv run pytest`: **508 passed, 1 existing skip**, exit 0.
- No production build, new E2E suite, full accessibility audit, graph rebuild or
  publication was performed. Browser inspection used live local read-only data.
- Raw screenshots, scripts, measurements and logs remain ignored under
  `reports/runs/WORK-2026-11-09-017/`. No application fixes were made.

## Acceptance targets for a later implementation

- At 1440px the graph leads; opening details is intentional. At 768px and 390px,
  the graph/list remains usable and every required control is reachable.
- Working labels meet 4.5:1 text contrast, no text is below 11px, selected/hovered
  graph labels remain readable in both themes, and forms follow the active theme.
- No chart legend overlaps ticks; chart layout follows available container width.
- Search → select → inspect evidence works with pointer and keyboard; replacing
  the quick entity strip retains an accessible alternative to canvas interaction.
- Preserve metric definitions, source access, the five entity labels, ten predicates,
  evidence distinctions, scientific limitations and frozen results.
