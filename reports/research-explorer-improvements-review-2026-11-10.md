# Research Explorer — improvement verification review

Reviewed 10 November 2026, Asia/Bangkok, against `41852c6` and
[the improvement plan](../docs/research-explorer-improvement-plan.md), using
`design-taste-frontend` app-screen rules. Review only; application files unchanged.

## Verdict

Keep the new visual direction. Soft graphite resolves the harsh black/white
appearance, desktop relationships are easier to trace, and current quality
figures are more consistent. The plan is **partially complete**: responsive
navigation, phone graph spacing, overlay accessibility and missing-data behavior
still need work. Passing automated style checks does not establish usability.

## Findings, in priority order

### 1. High — tablet header controls block workspace navigation

At 768px, Paths overlaps Table and Compare overlaps Analytics. Ordinary Playwright
clicks time out because those tools intercept the pointer. At 1024px, Analytics
is also covered by Paths; a separate direct-click check reproduced the failure.
At 390px, the tools menu covers the right end of Analytics, although its center
remains clickable. The initial Graph header also clips product/version copy.

The single nonwrapping flex row combines nonshrinking identity, search, tabs and
tool groups. See `TopHeader.tsx:163–251`. Reflow navigation into its own row or
collapse secondary tools/version earlier. Test real pointer navigation in both
initial and selected states at each width; checking header height is insufficient.

Evidence: `review-captures/graph-768-dark.png`, `capture-review.log`,
`focused-review.json`, `targeted-review.json` in the run directory below.

### 2. High — absent evidence still produces measured-looking quality scores

Calling `_build_quality_contract()` with all five artifact dictionaries empty
returns edge precision **96.5%, 193/200, status passed**, plus historical Wilson
bounds, coverage and topic values. This was reproduced in memory without changing
files or the database. The current live artifacts exist and the principal live
scores agree with the release; this finding concerns missing/incomplete evidence.

`backend/services/explorer_service.py:148–297` supplies historical defaults instead
of unavailable states. `AnalyticsView.tsx:193–195,469–573` also retains fixed counts
and PASS/FAIL copy. Return unavailable values/statuses with provenance when facts
are absent; derive all displayed status text and counts from the contract. Verify
missing and alternative values, not only today's release snapshot.

Evidence: `missing-quality.json`. This violates the plan's explicit requirement
that missing source facts stay unavailable.

### 3. Medium — phone node collisions still obscure relationships

At 390×844 the canvas is now **390×597**, starting at y=208: the sizing objective
passes. However, Warut and Dongxiao neighborhoods merge into large colored blobs;
individual nodes and intervening edges cannot be read. The same problem appears
in both themes. Large empty margins coexist with a compressed drawing.

`lib/colors.ts:233–249` sizes nodes without viewport input. Display layout spacing
alone does not prevent fixed-size nodes overlapping when the graph scales down.
Use viewport-aware sizing and collision spacing together, or provide an explicit
smaller default slice with its scope visible. Preserve membership/evidence when
changing presentation. Do not solve this solely by reducing edge contrast.

Evidence: `graph-390-dark.png`, `graph-390-light.png`.

### 4. Medium — drawer and picker accessibility remains incomplete

Opening the phone filter drawer leaves focus on its header toggle; the next Tab
goes to background Search. The drawer has no dialog role or modal state and does
not make the background inert. Escape does close it. See
`components/filters/LeftSidebar.tsx:209` and the overlay branch in
`components/inspector/RightInspector.tsx:145`; overlay drawers need the same
initial-focus, containment and return behavior as modal workflows.

In Paths, the focused picker search input has no accessible label, combobox role,
controls or active-descendant association. Those attributes sit on the unfocused
trigger instead (`EntityPicker.tsx:218–275`). ArrowDown/Enter selects Warut correctly,
but the focused field does not expose that active option to assistive technology.
Complete the editable-combobox semantics and verify with an accessibility tree.

The Paths modal itself improved: initial focus enters, Shift+Tab wraps, background
is inert, Escape dismisses the picker before the dialog, and focus returns to Paths.
These checks do not establish that every other modal is fully accessible.

### 5. Medium — Strong links can silently display every link

`SigmaGraphCanvas.tsx:234–240` substitutes the complete edge list when the strong
filter finds no matches. A zero-match result therefore looks like successful
filtering. In the browser citation view, selecting “Strong links (≥2 papers)” left
all 43 displayed links visible. Read-only citation API samples had zero qualifying
strong edges. The filter also accepts fractional weight ≥0.45 despite its label
mentioning only paper count.

Keep zero results as zero and explain them. Either define a projection-appropriate
filter or disable it with an explanation where shared-paper strength is inapplicable.
Display counts must describe the actual filtered result.

## Further design polish

- Desktop organization links still form a bright mesh. Strengthen the selected
  relationship hierarchy before adding more legend detail.
- Phone Analytics stacks four inventory rows before the quality summary; its first
  chart starts around y=530. A compact 2×2 inventory strip would bring useful analysis
  higher. The topic failure is truncated in the collapsed quality summary; preserve
  a short explicit failure label rather than hiding it in the clipped tail.
- Phone Table has a sticky identity column and local scrolling, but long names/IDs
  truncate and the trailing action starts clipped. A two-line row or a slightly
  better column allocation would improve scanability.
- After explicitly closing filters at 1440px, resizing to 768px and back reopens
  them. This was reproduced with time for each resize event; `App.tsx:97` overrides
  the user's prior choice. The plan explicitly asked to preserve it.
- Small text remains prevalent: production inspection flags about 39% at 12px or
  below. Reserve that density for IDs/metadata; use larger working labels where
  people choose entities and compare evidence.

## Plan acceptance snapshot

| Area | Current result |
| --- | --- |
| Softer dark appearance | Achieved in reviewed screens; neutral ground/surfaces and softer working text/buttons |
| Development/production parity | Reviewed header colors match on :5173 and fresh :4173 |
| Current quality figures | Principal figures and targets corrected; unavailable/dynamic cases fail |
| Responsive workspace | Phone plot and selected tablet graph sizes pass; header navigation fails |
| Graph readability | Desktop researcher/citation views improved; phone collisions remain |
| Keyboard workflows | Paths/modal layers improved; overlay drawers and picker semantics incomplete |
| Retrieval | `Tuomas Sandholm` returns stored `Tüomas Sandholm`, with stable ID preserved |
| Theme/state | Explicit light preference survives reload; user-closed rail reopens on resize |

At 1024/1100px, selecting a node folds filters and leaves 632/708px of graph width.
At 1280/1440px, both rails leave 616/776px. Inspector is absent from Table in all
six width checks. No page overflow or page exceptions appeared in the completed
focused script. Full WCAG compliance, every contrast pair, screen-reader output,
reduced-motion behavior and both themes at every width were not exhaustively tested.

## Fresh verification and evidence

All results below were performed in this review, not copied from WORK-001.

| Check | Result |
| --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report` | Exit 0 |
| `uv run pytest` | 508 passed, 1 existing empty-parameter skip; exit 0 |
| `PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -v` | 14 passed; exit 0; Starlette/httpx deprecation warning |
| `npm --prefix apps/research-explorer/frontend run build` | Passed; Vite large-chunk warning, JS 1,561.14kB raw / 481.56kB gzip |
| `PLAYWRIGHT_BASE_URL=http://127.0.0.1:4173 npm --prefix apps/research-explorer/frontend run test:e2e` with unique screenshot directory | 4 passed; exit 0 |
| Skill `lint.mjs --app` on frontend | 0 FAIL, 36 WARN, exit 0; mono occurrences need context, IDs/code are permitted |
| Skill `inspect.mjs --app` on :5173 / :4173 | 0 FAIL, 2 WARN / 0 FAIL, 1 WARN; dev-server warning and small type / small type |
| Custom browser checks | Real navigation failures reproduced despite existing E2E passes; completed width/keyboard/state checks recorded |
| Missing quality dictionaries | Historical numbers and passing statuses reproduced; acceptance failure |

All inspector fold/contact images at 1440,768,390 were opened for both servers.
Additional screenshots cover all four desktop projections, selected node/edge,
Analytics, Table, Search, Paths, Compare, Caveats and phone light mode. Custom
screenshots are local evidence, not a complete two-theme/six-width acceptance matrix.

Initial supplemental capture stopped at the genuine 768px Analytics interception.
The first focused script also stopped at blocked Table; a revised script caught
that failure and continued through the remaining checks. A targeted-script selector
typo was corrected before the final recorded run. These were not clean full runs.

Raw logs/scripts/screenshots: ignored
`reports/runs/WORK-2026-11-10-002/`.
Production preview started for this review remains available at `127.0.0.1:4173`.
No app implementation, graph writes, source collection, public Site change,
publication or push occurred.
