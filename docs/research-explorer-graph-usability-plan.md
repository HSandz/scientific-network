# Research Explorer — combined graph and website improvement plan

Prepared 10 November 2026. **Planning only; no application implementation yet.**
Based on [the website verification review](../reports/research-explorer-improvements-review-2026-11-10.md)
and [the graph operations review](../reports/research-explorer-graph-operations-review-2026-11-10.md).
This is the current combined implementation handoff; the earlier
[improvement plan](research-explorer-improvement-plan.md) remains historical context.

## Intended result and boundaries

A researcher can identify a node and its neighbors together, follow a connection,
inspect evidence, expand or isolate a neighborhood, and return without losing their
place. Counts, filters, exports and shared views describe the graph actually shown.

Retain React/TypeScript, Sigma, ECharts, the current visual identity and both themes.
Use `design-taste-frontend` **app-screen** rules, with the user's soft graphite
preference taking precedence over stock black/white dark examples. Preserve the
neutral `#1e1e1e` ground, `#252525` surface, `#cecece` working text and restrained
`#7fa6cc` focus accent, checking actual contrast instead of assuming tokens suffice.
No new decorative gradients, bright white primary blocks or navy surfaces.

Implementation scope: `apps/research-explorer/`, its focused checks and normal work
records. Read-only API changes are allowed where needed for correct scope, retrieval
or provenance. No corpus changes, graph writes, recollection, re-audit, threshold
retuning, new centrality/community computation, frozen-artifact replacement, public
Site update, publication, push or release-package change. Same-name researchers
remain distinct stable IDs. Display layout changes never alter scientific edges.

## 1. Establish correct view state and preserve every relationship — first

Addresses G02–G06, G08–G09 and earlier count/filter concerns.

- Define explicit **Overview**, **Neighborhood** and **Path** views, with a clear
  title/scope and Back to the preceding view. Append and replace must be distinct
  operations; `focusedCenterId` must actually affect the rendered view.
- Derive one effective node/edge set after mode, scope and presentation filters.
  Feed canvas, visible-neighbor list, displayed metrics, legend and exports from
  that same set. Retain API provenance and full-projection metrics separately.
- Replace unordered endpoint-pair suppression with stable edge-ID handling. Use
  renderer support for parallel and reciprocal edges; distinguish opposite arrows
  with curved/offset lanes. Preserve direction, predicate, evidence kind and ID.
  A visual bundle must disclose its multiplicity and offer every member edge.
- Compute “visible degree” and strength from the final displayed edge set after
  expansion/filtering. Distinguish neighbor count from edge count when several
  relationships share endpoints. Never reuse base payload degree as rendered degree.
- On layout changes, reapply selection/hover reducers. On projection/filter changes,
  clear hover and either preserve a selection that exists in the new slice or show
  an explicit off-canvas state without dimming the entire graph. Do not leave an
  unrelated researcher's inspector masquerading as the organization selection.
- Protect transitions from late responses: cancel or ignore expansion/path responses
  that belong to a previous mode or scope. This is a required regression case, not
  a claim that the race was reproduced in the review.

Likely files: `App.tsx`, `stores/useExplorerStore.ts`, `SigmaGraphCanvas.tsx`,
`RightInspector.tsx`, graph types and API response mapping where needed.

Acceptance: every accepted effective edge ID is represented; reciprocal edges
remain individually inspectable. Header counts, visible metrics, neighbor list
and export agree before/after all tested operations. A zero-match filter stays zero.

## 2. Make hover and pinned neighborhoods understandable — main user-facing change

Addresses G01 and dense-graph readability.

- **At rest:** keep a restrained overview label set. This is the right place for
  label thinning; do not force every node name onto the overview.
- **Hover:** emphasize the center and immediate incident edges. Give the center
  and its first-hop neighbors priority labels using full source names where space
  allows. Use multiple label placements/leader lines and collision checks rather
  than letting the normal overview grid suppress nearly every neighbor name.
- For the reviewed seven-neighbor example, all seven neighbor names must be readable
  together at the normal desktop view without hovering each endpoint. The center
  must remain identifiable, and names must not overlap other names or disappear
  beyond the canvas edge.
- For high-degree nodes such as the 53-neighbor organization example, provide an
  automatically visible neighbor summary with an explicit total and a clear way
  to pin/open the complete list. Never silently label one endpoint and imply it
  is the only connection; never print 53 overlapping labels.
- **Click/tap:** pin the neighborhood. Keep its labels/list stable while the pointer
  moves to read or select neighbors. Distinguish transient hover from a pinned
  selection; Escape or a clearly labelled action clears the relevant layer.
- Add an **On this graph** neighbor list in the inspector/sheet. It contains all
  currently visible neighbors, supports name/type/predicate filtering and sorts by
  a labelled rule. Show full names/titles, relationship direction, paper support or
  weight where applicable, and evidence access. Pair list focus with canvas emphasis.
- Keep **All database connections** a separately labelled scope. The current global
  grouped list is not the same as the highlighted neighborhood; bounded results
  need “showing N of M” plus a way to fetch more where supported.
- Pointer, touch and keyboard must reach the same information. Focusing a neighbor
  row previews its node/edge; Enter selects; no operation depends on hover alone.

Likely files: `SigmaGraphCanvas.tsx` custom renderers/reducers, inspector/list,
selection store and optional shared focus-label helper.

Acceptance: Warut 7/7 names; the reviewed topic's 28 neighbors and organization's
53 neighbors are all obtainable in the correctly scoped list. Name truncation on
canvas always has a full-name alternative; moving to the pinned list does not
change the center. Test long names, same-name IDs, isolates and edge endpoints.

## 3. Give expansion, Ego and Paths truthful behavior and a return route

Addresses G02–G03, G07, G09–G10.

- **Expand +1 hop** adds only neighbors allowed by the current projection and active
  filters, preserving existing positions and camera when possible. Show how many
  distinct nodes/edges were actually added, plus any truncation/limit.
- **Ego view** replaces the overview with the center and its bounded neighborhood;
  fit that neighborhood deliberately. Back restores prior scope, selection,
  positions and camera. A second expansion in Ego remains in that view.
- Provide an explicit **Explore all relationship types** action when useful. Switch
  title, key, filters and metric explanations to a mixed graph before displaying
  Paper/Organization edges inside a former researcher-only projection.
- **Show path** opens a dedicated path view: ordered, named nodes; predicate and
  direction at each step; visually emphasized path; evidence per step. Background
  context, if offered, is explicitly toggled and counted. Preserve any traversal
  caveats from the response; a traversal must not imply every step follows a
  directed relationship forward. Back returns to the previous graph.
- Keep expansion request limits bounded. Say “showing N of M” using compatible
  counts; do not compare an edge total with a unique-neighbor limit as if identical.
- On failure, keep the last good graph and show a concise inline error with Retry.
  Expose loading status to assistive technology. Do not silently log failures.

Likely files: App/store, `PathFinderModal.tsx`, inspector actions, API parameters
and neighborhood metadata where required. Reuse the existing read-only service.

Acceptance: Ego excludes unrelated base nodes; the reviewed path is legible as
three nodes/two steps. Expanding Researchers retains researcher/COAUTHORED_WITH
scope unless the user explicitly changes it. Simulated 503 has visible Retry.

## 4. Improve layout, edge reading and camera continuity

Addresses G07/G11, website mobile collisions and organization mesh density.

- Make node sizing and collision spacing viewport-aware in the **active inline
  sizing code** in `SigmaGraphCanvas.tsx`, not only the unused radius helper.
  Preserve a minimum gap at the reviewed default zoom and reserve room for labels.
- Preserve existing nodes when adding neighbors, place new nodes near their parent,
  and avoid mixing incompatible layout coordinate systems. Offer Fit graph and
  Fit neighborhood as explicit actions instead of refitting every update.
- Preserve camera state across theme, selection and filter changes where the
  visible scope survives. When a deliberate new view needs a fit, make Back restore
  the old camera. Dragged positions are presentation state, with a clear reset.
- Keep Force as a deterministic overview. Rework or remove overlapping Circle and
  Radial variants; explain their ordering/rings if retained. Rings must not imply
  communities, hierarchy or relationships that the data does not establish.
- For dense organization views, use a truthful overview plus pinned neighborhood
  focus and optional explicit strength filtering. Show filtered counts and a reset;
  do not silently remove weak edges to make the screenshot look cleaner.
- Add edge hover/focus information: source, predicate, target, direction, evidence
  kind and the correct support/weight unit. Clicking an edge opens evidence.
  Mixed graphs must visibly distinguish inferred-topic relations from observed,
  curated and derived relationships through a restrained, labelled visual key.
- Keep contrast sufficient for meaningful nodes/arrows/focus on graphite and light
  backgrounds. Quiet context is useful, but must not become an unreadable field.

Acceptance: all four reviewed projections remain usable at 390/768/1024/1100/1280/
1440px; connected nodes are distinct at default zoom. Zoom → select → expand does
not unexpectedly reset the camera. Parallel edges remain separately selectable.

## 5. Make filters, export, share and saved views consistent

Addresses G08 and operation reproducibility.

- Remove “show everything” fallbacks from Strong links and Hide isolates. Provide
  honest empty states and a reset. Define strength per projection; disable an
  inapplicable paper-support filter on Citations instead of pretending it succeeded.
  Labels must match both support-count and fractional-weight rules if both remain.
- Export the effective displayed graph, with applied filters, graph/method version,
  metric scopes and timestamp. If exporting a broader payload is useful, name it
  explicitly as a separate action. Keep CSV/JSON identities and counts consistent.
- Version and round-trip relevant view state in shared URLs/bookmarks: projection,
  scope filters, limit, layout, visible-edge filter, selected entity, and dedicated
  Ego/path state where supported. Validate URL input. If a state cannot be shared,
  disclose the limitation instead of calling the result an exact saved view.
- Preserve user choices when switching tabs/resizing. A deliberately closed filter
  rail stays closed; stale selection does not cover/dim unrelated projections.

Likely files: store URL/bookmark helpers, header export/share handlers, graph filters.
Acceptance: the reviewed 54-edge filtered graph exports 54 edges and reloads with
that filter; a zero-match result remains empty and is exported/shared as such.

## 6. Finish the surrounding website fixes from WORK-002

- **Header:** give primary navigation sufficient room at every width. Collapse
  version/secondary tools earlier or use a separate navigation row. Table and
  Analytics must accept ordinary pointer clicks at 768/1024px, including selection
  states; no overlap, clipped name, or undersized mobile targets.
- **Phone tools:** move layout, edge filters, focus/clear and relevant scope controls
  into reachable sheets/menus. Tap pins details; provide a neighbor list and Back.
  Preserve the large graph area without shrinking working text or touch targets.
- **Quality:** remove historical numeric defaults for missing evidence. Use
  unavailable states with provenance. Derive all numerators, denominators, targets
  and pass/fail text from the canonical contract; test alternative values. Preserve
  AI-assessed labels and all human-validation limitations and known failures.
- **Accessibility:** modal overlay drawers get initial focus, contained Tab,
  appropriate semantics, inert background, Escape layering and focus restoration.
  Editable entity pickers expose label, combobox/listbox and active option from the
  focused input. Preserve the Paths modal behavior already verified as working.
- **Analytics/Table:** compact phone inventory into a useful 2×2 strip or equivalent;
  keep affiliation/topic failure summaries visible without clipping; raise working
  labels above metadata size where appropriate. Improve mobile identity rows and
  access to their trailing action while preserving sortable metrics and source IDs.
- **Theme:** retain the softer dark palette across canvas, charts, tooltip, dialogs,
  hover and focus. Verify reload/system preference behavior and reduced motion;
  these were not exhaustively certified by the review.

## 7. Verify the user's tasks, not only style measurements

Add focused regressions for the confirmed failures. Do not snapshot every CSS rule
or treat invented test fixtures as measured research results. A minimal matrix:

| Task | Required observable result |
| --- | --- |
| Hover and pin Warut | Center plus 7 neighbor names readable together at desktop; list has exactly those visible neighbors |
| Hover/pin dense org and topic | Full named list available, honest total, no overlapping label wall |
| Filter then inspect | Header, actual edge IDs, neighbor list, degree/strength and export agree |
| Reciprocal/parallel edges | Every distinct edge ID retained with correct direction/predicate/evidence |
| Ego → Back | Only bounded neighborhood shown; prior overview/camera restored |
| Expand under active scope | Scope respected, actual additions counted, truncation disclosed |
| Show path → Back | Ordered named steps emphasized; no misleading projection key; prior state restored |
| Layout/theme change | Selection and evidence focus persist; graph remains readable |
| Projection change | No stale hover, all-dim graph, or misleading unrelated selected inspector |
| Share/bookmark reload | Supported scope/filter/layout state restored exactly |
| Expansion fails / response arrives late | Visible Retry; previous graph retained; stale response ignored |
| Mobile/tablet navigation | Real clicks work; graph tools reachable; drawer keyboard/touch workflows usable |
| Missing/alternative quality facts | Unavailable stays unavailable; dynamic values and statuses agree across views |

Run required repo/backend checks for implementation, a relevant offline CLI check,
TypeScript/build, focused Playwright checks and read-only Neo4j integration where
query behavior changes. Use skill `lint.mjs --app` and `inspect.mjs --app` on fresh
dev/production, open every generated fold/contact sheet, and inspect actual graph
states in both themes. Existing E2E passes did not catch these bugs.

At the six widths, check initial, selected and pinned-neighborhood states; examine
all four projections, long labels, isolates, empty filters, mixed/reciprocal edges,
paths, errors, reduced motion and keyboard access. Verify text ≥4.5:1 and essential
graph/focus states ≥3:1 on actual surfaces. Record any valid semantic-color/ID-mono
exceptions to the skill; keep the user's softer-dark choice.

Handoff: bounded changed-file summary, exact fresh results/skips, before/after
screenshots, edge/count parity evidence, unresolved limits, updated app docs/work
records and preservation checks. This plan authorizes no app edits in the current
review; a later implementation request can use it directly.
