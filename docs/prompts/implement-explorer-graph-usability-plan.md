# Fresh-session prompt — implement the Research Explorer usability plan

Copy this prompt into a new coding-agent session:

```text
You are working in /home/san/Code/scientific-network. Implement the user's
combined Research Explorer improvement plan in this repository. This prompt
explicitly authorizes local application changes in the bounded scope below. Do the
implementation and verification; do not stop at another review or plan, and do not
ask for routine approval.

## Read first

At session start, read in this order:
1. AGENTS.md
2. docs/release-plan.md
3. docs/status.md
4. The latest docs/work-log/ entry

Then read the complete implementation specification and evidence:
- docs/research-explorer-graph-usability-plan.md — authoritative combined plan
- reports/research-explorer-graph-operations-review-2026-11-10.md — graph
  operations findings and reproductions
- reports/research-explorer-improvements-review-2026-11-10.md — earlier website,
  responsive, dark-mode, quality-contract and accessibility findings
- apps/research-explorer/README.md and relevant source/tests

Use the `design-taste-frontend` skill. Read
/home/san/.agents/skills/design-taste-frontend/SKILL.md and
/home/san/.agents/skills/design-taste-frontend/references/app-screens.md in full.
This is a working data application: follow the app-screen workflow, run its app
lint and real-browser inspector, open every generated fold/contact sheet, critique
what you see and fix the most important remaining issues. Keep the existing product
identity and the user's soft graphite preference. If the skill path moved, locate
it; do not silently skip the requested skill.

Verify the actual Git state, protected/untracked files, running services, current
app architecture and test commands before editing. Earlier logs and inspection
scores are historical. Preserve all existing staged, unstaged and untracked work,
including the recent review/plan documents. Inspect nested instructions. Create a
new unused work-log entry from docs/templates/work-log.md using the actual
Asia/Bangkok date. Record the objective early and update the log, index and
replacement docs/status.md as you progress.

## User goal

Make Research Explorer a clear, reliable workbench for following research-network
relationships. The user specifically finds it annoying that hovering a node
highlights connected nodes without naming them; currently they must hover each
neighbor. Keep the softer dark appearance introduced in the previous pass, and
fix the graph operations and website findings documented in the linked reports.

The hover measurements are representative cases at 1440x900, not claims about all
nodes: Warut Suksompong had 7 visible neighbors but only 1 neighbor name drawn;
Representation learning had 28 neighbors and 1 name; Zhejiang University had 53
neighbors and 10 names; the small Informer citation example showed both of its 2
neighbor names. Reproduce against current source/data because this checkout may
have moved. Do not turn these examples into invented dataset-wide statistics.

## Boundaries

Keep the existing React/TypeScript, FastAPI, Sigma.js and ECharts stack. Application
work belongs primarily in apps/research-explorer/. Necessary read-only API changes
are in scope. Keep dependencies minimal and lockfiles synchronized if a dependency
is necessary.

Preserve the D040 release graph, corpus, five entity labels, ten predicates, stable
IDs, directions, evidence, weights, frozen audit/splits/results, release thresholds,
Neo4j data, public Site and submission package. Change no graph membership or
scientific meaning to improve the picture. Display-only layout changes are allowed;
do not rewrite frozen layout artifacts or recompute scientific centrality/community
results. Never merge researchers by normalized names. Keep observed, inferred,
curated and derived evidence distinct. Do not collect sources, rebuild/import the
graph, alter release thresholds, re-audit, publish, push or submit. The app remains
read-only against the isolated neo4j-five-year database. Do not log credentials or
private source text.

## Implementation sequence

Implement all sections of docs/research-explorer-graph-usability-plan.md. Use this
sequence to keep correctness ahead of polish:

1. **Make the rendered view authoritative.** Establish one effective graph state
   after projection, scope and display filters. Canvas, node/edge counts, legend,
   visible-degree/strength metrics, neighbor list, exports and shareable state must
   describe that same view. Keep full-projection scientific metrics clearly separate.
   Preserve every distinct stable edge ID, including reciprocal and parallel edges;
   show direction and predicate clearly. Do not collapse edge identity in the
   renderer. Fix the stale selected-node inspector counts.

2. **Add stable, useful neighborhood reading.** Keep overview labels selective. On
   hover, identify the center and its immediate relationships together. For a
   moderate neighborhood, arrange all neighbor names legibly without requiring a
   second hover. For dense nodes, do not print a wall of overlapping labels: show
   an explicit neighbor total and make the complete, searchable/selectable list
   immediately available. Clicking/tapping pins the center and its neighborhood so
   moving to the list does not change focus. The list must offer full names, IDs
   where needed to distinguish same-name people, entity type, relationship/predicate,
   direction, support/weight with units, and evidence access. Keyboard users must
   reach the same information. Name truncation always has a full-name alternative.

3. **Make Overview, Ego/neighborhood, and Path explicit views.** Ego replaces the
   overview with only its bounded neighborhood and provides Back that restores the
   prior scope, selection, positions and camera. Expand +1 hop respects the current
   projection and active filters by default; do not silently mix paper and
   organization predicates into a researcher projection. If the user chooses to
   explore all predicates, update title, legend, scope, filters and metric labels.
   A path opens a named, ordered path view with each predicate, direction and
   evidence available. Its key must match the mixed entity types. Keep the prior
   graph available through Back. Bound requests, report truncation honestly, keep
   the last good view on errors and show an inline error with Retry. Ignore stale
   responses after scope/mode changes.

4. **Fix layout, selection and camera behavior.** Retain selection highlighting
   after Force/Radial/Circle changes. On projection changes, clear transient hover
   and either clear a selection that is outside the new view or show it explicitly
   as off-canvas; never dim an unrelated graph because an old entity remains
   selected. Preserve zoom and existing positions during expansion where possible;
   place additions locally. Fit graph and fit neighborhood should be explicit
   actions. Make the active inline Sigma node sizing and spacing responsive to
   viewport; confirm which sizing code the renderer actually calls. Rework/remove
   Circle/Radial if nodes overlap; layouts must not imply unsupported community or
   hierarchy meanings. Make dense organization graphs readable while retaining
   explicit totals and filters.

5. **Make filters, export and share truthful.** A filter with no qualifying edges
   returns zero and a clear empty state, never all edges as fallback. Define
   projection-appropriate strength rules; disable or explain inapplicable controls.
   Export the effective displayed nodes/edges and attach applied scope, graph/method
   version and relevant metric scopes. If broader export is useful, label it as a
   separate action. Shared URLs/bookmarks round-trip supported projection, scope,
   limit, layout, display-edge filter, selected entity and focused view; disclose
   anything that cannot be shared.

6. **Finish the website issues from the previous review.** Fix header hit-target
   overlap so Graph/Table/Analytics accept ordinary pointer clicks at 768px and
   1024px, including selected states. Collapse version/secondary controls sooner
   or reflow navigation. At phone widths keep product/scope, search and workspace
   navigation clear; put layout, edge filters and secondary graph tools in reachable
   menus/sheets with usable touch targets. Fix the quality contract so absent
   artifacts render unavailable, never historical-looking numeric defaults or
   success statuses. Derive counts, denominators, targets and status copy from the
   shared source; preserve AI-assessed caveats and current failures. Give overlay
   drawers correct focus entry/containment, dialog semantics, inert background,
   Escape layering and restoration. Give the focused editable entity-picker input
   an accessible label and valid combobox/listbox active-option semantics. Keep
   phone Analytics quality failures visible and improve the phone table's identity
   and trailing action access. Preserve the verified softer graphite palette and
   readability in both themes.

The plan's precise paths and acceptance details are in
`docs/research-explorer-graph-usability-plan.md`; use it as the full specification.
Do not silently narrow scope. If a planned behavior conflicts with graph evidence,
release constraints or actual runtime, document the exact conflict and implement
what is safe and supported while continuing independent work.

## Acceptance checks

Add focused regressions for reproduced behavior; do not write snapshots for every
CSS token or tests that merely mirror the implementation. At minimum demonstrate:

- Warut's seven visible neighbor names can be read together or from the pinned
  neighbor list without hovering each neighbor. Dense topic and organization
  neighborhoods expose every visible neighbor by name without label overlap.
- The focused list corresponds to the highlighted graph neighborhood, while
  database-wide connections are clearly identified as a different scope.
- Every distinct edge ID is retained after expansion; reciprocal directions and
  parallel predicates remain inspectable. Counts and visible metrics match the
  effective graph after filters and expansion.
- Ego excludes unrelated overview nodes; Back restores the prior graph/camera.
  Expansion follows active projection/scope and reports additions/truncation.
- Layout/theme changes retain appropriate selection; projection changes do not
  leave stale hover or dim an unrelated graph. Zoom then expand does not reset
  unexpectedly.
- Paths show named ordered steps and evidence, then return to the previous graph.
  A simulated neighborhood API failure displays Retry and keeps the old graph.
- Strong-link zero results remain empty. The filtered edge set in the canvas,
  counts, JSON/CSV exports and shared URL agree after reload.
- Header clicks work at 390, 768, 1024, 1100, 1280 and 1440px. Graph controls are
  reachable on phones. Overlay drawers and pickers pass keyboard/accessibility
  checks.
- Missing quality artifacts remain unavailable; alternative valid inputs produce
  matching values and statuses across Analytics, Caveats, header and README.
- At all six widths, inspect both themes, initial and selected states, all four
  projections, hover/pin, dense organization and heterogeneous views, evidence,
  table, analytics, modal/drawer states, overflow and console errors. Check the
  actual rendered contrast; text >=4.5:1 and essential focus/graph states >=3:1.

Follow AGENTS.md and docs/release-plan.md for the exact current repository checks.
Run the repository suite, relevant backend tests/read-only Neo4j integration if
query behavior changed, a relevant offline CLI check, frontend TypeScript/build,
existing and focused Playwright flows, and the design skill's app lint/inspector.
Use fresh dev and production preview builds. Open every fold/contact sheet and fix
what the browser still shows. Record skips, warnings, failed checks and unavailable
integrations truthfully; E2E passing alone is not evidence that the reproduced
pointer/graph bugs are fixed.

Store raw evidence under a unique ignored `reports/runs/WORK-.../` directory. Update
app docs, the work log/index and docs/status.md (keep it under 60 lines). Preserve
all existing work and stage only this task's files. Commit locally only at an
applicable project checkpoint under AGENTS.md; never push or publish. Finish the
implementation and verification in this session with a concise changed-file
summary, before/after evidence, exact checks and outcomes, remaining limits, and
confirmation that protected graph/release artifacts were preserved.
```
