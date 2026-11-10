# Research Explorer improvement plan

Prepared 9–10 November 2026 for the user's request; **proposed, not implemented**.
Basis: [follow-up review](../reports/research-explorer-redesign-review-2026-11-09.md).
Execution handoff: [fresh-session prompt](prompts/implement-explorer-improvements.md).

## Outcome and scope

Make the existing Explorer comfortable for sustained research work: find an entity,
read its relationships, inspect evidence. Retain React/TypeScript, Sigma, ECharts,
the recognizable layout, both themes and existing functionality. Apply
`design-taste-frontend` **app-screen** rules. The user's softer-dark preference
takes precedence over generic skill examples of black surfaces and white text.

Implementation belongs primarily in `apps/research-explorer/`. Small read-only API
changes for shared quality facts, retrieval and display layout are in scope.
Preserve unrelated work, graph membership/weights/evidence, corpus, frozen results,
thresholds, public Site and release package. No recollection, rebuild, re-audit,
Neo4j writes, model downloads or public deployment. Missing source facts remain
unavailable; never substitute invented numbers. This plan adds no release gate.

## 1. Establish one reliable baseline and one source for quality facts

- Capture the Git state, preserve the existing staged/unstaged work and record
  current UI screenshots before editing. Read WORK-019; its results are historical.
- Reproduce the `:5173` / fresh `:4173` appearance mismatch. Trace served CSS,
  Tailwind tokens/configuration and process state. Restart only the identified app
  server if needed; never broadly kill processes. Resolve the cause before styling.
- Trace summary/configuration → API → Analytics/Caveats → README. Return structured
  counts, denominator definitions, targets, status and version/provenance from one
  source, and format them consistently in both views. Replace duplicated display
  constants with values from that contract; test with values other than today's.
- Current release evidence to verify: affiliation counts are 48,259 / 65,469,
  not Analytics' 37,199 / 50,466. Read `reports/release-v4/graph-summary.json` and
  the active quality config; the current coverage target is 80%, topic-label
  precision target 95%, and topic coverage target 80%. Do not create a 0.80 F1 gate
  or label 85% coverage as failed against an invented 90% target. Keep topic
  precision failure distinct from coverage and historical F1 measurements.
- Preserve AI-assessed labels, confidence intervals, human-validation limitations,
  affiliation failure, observed/inferred/derived distinctions and metric scopes.
  Correct contradictory copy in the app README within this same scope; do not
  rewrite historical release evidence.

Likely files: backend config/models/service, `lib/api.ts`, `types/explorer.ts`,
`AnalyticsView.tsx`, `CaveatsModal.tsx`, `TopHeader.tsx`, app README.

## 2. Soften dark mode across CSS, graph and charts

Use **soft graphite**: lift the darkest surfaces, reduce the brightness of working
text and remove repeated near-white button fills. Keep the neutral palette; no
navy wash, glow, transparency effects or decorative gradients. Keep light mode's
current identity. The values below are concrete starting tokens, to verify on the
rendered interface rather than apply mechanically:

| Role | Proposed dark value | Purpose |
| --- | --- | --- |
| Ground / graph canvas | `#1e1e1e` | Replace the near-black field |
| Surface | `#252525` | Header, filters, evidence and cards |
| Raised / hover | `#2d2d2d` | Gentle elevation and hover feedback |
| Active / emphasized control | `#363636` | Selection and filled actions without white blocks |
| Structural border / chart grid | `#373737` / `#323232` | Quiet grouping; omit lines when a tone step suffices |
| Control outline | `#5b5b5b` | Distinguish controls without bright outlines |
| Main text / chart labels | `#cecece` | Softer than the current near-white |
| Secondary text | `#b0b0b0` | Explanations and labels |
| Metadata / placeholder text | `#9f9f9f` | Readable IDs, dates and sublines |
| Data / focus accent | `#7fa6cc` | Restrained blue for selected data and keyboard focus |

Nominal sRGB calculations give main text 10.59:1 on ground and 9.74:1 on surface;
metadata is 4.57:1 even on the proposed active fill. These are token calculations,
**not browser-validation results**. Check actual surfaces, opacity and hover states.

- Avoid pure `#000` / `#fff` in ordinary dark surfaces, text, tooltips and controls.
  Make primary actions a raised graphite fill with a clear label, border and state;
  selected navigation uses tone and weight. Keep the focus ring visible.
- Define graph labels, hover labels, selected node rings, chart axes/series,
  tooltips, sliders and native form controls from shared semantic tokens. Replace
  independent hard-coded near-white values in Sigma/ECharts. Preserve meaningful
  category and status colors, tuned to the softer ground and paired with text.
- Don't solve black/white harshness by dimming every relationship. Edge visibility
  must improve alongside surface softness. Use neutral context edges and the accent
  on focused connections; suppress visual noise through explicit focus states.
- All meaningful text remains at least 4.5:1. Essential graphical states/focus
  indicators reach 3:1 against adjacent colors; decorative dividers need not.
  Use size, spacing and weight to support hierarchy rather than luminance alone.
- Verify theme persistence, system preference when no explicit choice exists,
  reduced motion, keyboard focus and absence of a theme flash on reload.

Likely files: `styles/index.css`, Tailwind config, `lib/colors.ts`,
`SigmaGraphCanvas.tsx`, `AnalyticsView.tsx` and shared theme helpers as needed.

## 3. Give each screen and width enough working space

- Desktop: retain the compact filter rail and conditional inspector. Allow both
  rails only when at least **600px of graph width** remains. Otherwise fold filters
  or show details as an intentional drawer. At 1024/1100px never recreate three
  narrow permanent panes. Below about 1100px use the tablet composition.
- Phone: retain product/scope, search and Graph/Table/Analytics navigation, but
  collapse secondary tools (Paths, Compare, export, layout) into reachable menus or
  sheets. Put graph identity and one control row above the plot. Put full counts,
  technical predicate names, release hashes and legend detail behind labelled
  disclosures. Keep a concise visible scope/quality entry.
- Initial 390×844 Graph target: plot at least **422px high (50% of viewport)**,
  starting in the upper third. Avoid achieving this by shrinking labels or targets.
  Use 44px touch targets and 12px minimum metadata; aim for 14px working text.
- Collapse the long graph key into a compact “Key” disclosure; preserve accessible
  entity selection through search and a concise list. Selecting on a phone opens
  one detail region with Back, preserving the prior graph/scroll position.
- Respond to viewport changes after mount: resizing desktop to tablet must not
  unexpectedly open a blocking drawer. Do not reopen something the user closed.
- Make inspector state appropriate to each tab: switching to Analytics/Table
  restores the wide view while preserving the selection for return to Graph.
- Analytics: use compact label/value inventory rows or a 2×2 strip on phones;
  provide a concise visible quality summary plus full details. Keep failures and
  AI-assessed status visible. First chart heading/plot should appear in the initial
  844px viewport. At tablet widths avoid three cramped quality columns.
- Table: use two-line entity/relationship rows on phones, with key number and
  action visible; disclose other fields without losing access. If a full table is
  necessary, scroll only its frame and fix the identity column in place. Maintain
  sorting, pagination, IDs, metric scopes and evidence actions.

Likely files: App, header, sidebars, store, graph toolbar/key, Analytics and Table.

## 4. Make actual network relationships legible

- Diagnose node collisions and edge lengths at the current display coordinates;
  verify that counts and directions match the bounded payload before blaming color.
  Review all four projections, not only the default researcher view.
- Add deterministic collision-aware display spacing, resize-aware node sizing and
  component packing as appropriate. Use minimum visual separation so a connected
  pair's edge/arrow remains visible. Keep isolate placement recognizable; avoid a
  ring that looks like a relationship when no ring relationship exists.
- Selecting an entity emphasizes it, its visible neighbors and incident edges;
  keep context identifiable. The inspector's seven visible edges must be traceable
  visually in the reviewed example. Provide explicit “Focus neighborhood” / Back
  behavior rather than silently discarding nodes. For dense organization views,
  use hover/selection to reduce clutter; any edge filter is explicit and counted.
- Prioritize labels for selection, hover and key nodes; retain full names in
  accessible lists/details. Keep citation direction clear and legends accurate.
- Preserve node/edge IDs, payload membership, weights, scopes and evidence. Display
  positions/sizes are presentation only, with versioned deterministic layout settings
  if cached/configured; never overwrite frozen network-view artifacts. Do not
  re-compute scientific centrality/community results to improve the picture.

Likely files: `SigmaGraphCanvas.tsx`, `lib/colors.ts`, and the backend's read-only
display layout function if frontend-only adjustments cannot solve the collisions.

## 5. Complete keyboard and name-based workflows

- Give Search/Paths/Compare/Caveats labelled dialog semantics, initial focus,
  contained Tab/Shift+Tab, inert background and focus restoration. Escape closes
  the topmost popup/drawer first. Treat overlay drawers similarly; static desktop
  sidebars remain normal regions. Avoid overlapping modal focus traps.
- Make EntityPicker a proper combobox/listbox with labelled input, active option,
  Up/Down, Enter, Escape, loading/no-result/error states and stable ID selection.
  Fix stale labels when switching presets or editing an ID; resolve names from
  current data instead of treating a fixed demo dictionary as authoritative.
- Support accent-insensitive name retrieval: `Tuomas Sandholm` should find the
  stored `Tüomas Sandholm`. Preserve original source spelling, separate same-name
  entities, stable IDs and source metadata. Search normalization never authorizes
  researcher merging or graph/name correction.
- Keep query work bounded and read-only. Debounce/cancel requests and preserve
  exact ID/DOI/ORCID search. Choose a measured retrieval approach compatible with
  Neo4j Community; no new graph properties/index writes, full ledger parsing on
  every keystroke, silent top-100-only search or new search service.

Likely files: modal/search components, EntityPicker, store/App, repository search
queries or a small read-only lookup cache where justified.

## 6. Verify outcomes and hand off evidence

Implement in the order above, then run one integrated visual/interaction pass.
Add focused regressions for the confirmed failures, not tests for every CSS token.

| Check | Acceptance |
| --- | --- |
| Quality contract | Analytics/Caveats/API share values and units; config targets unchanged; README agrees; missing data not rendered as zero/success |
| Soft dark theme | No broad near-white controls or near-black canvas; actual text contrast passes on every used surface; graph/chart/modal/hover states share tokens |
| Width matrix | Both themes at 390, 768, 1024, 1100, 1280 and 1440px; selected and initial states; visible plot meets sizing goals; no page overflow |
| Graph | All four projections, selected node/edge, zoom and neighborhood expansion; no indistinguishable connected-node pileups at the default reviewed views; counts/evidence preserved |
| Keyboard | Open Paths by keyboard → focus enters → Tab stays inside → picker ArrowDown/Enter selects → Escape closes topmost layer → focus returns; repeat Search/Compare/Caveats/drawers |
| Data access | Accent query works, same-name candidates stay distinct, stable ID search works, table/inspector metric scopes still agree |
| Theme/state | Preference survives reload; no flash; resize does not unexpectedly cover workspace; tab changes preserve selection without unrelated inspector intrusion |
| Runtime | Fresh development and production CSS match; no console/page errors in exercised flows; build and focused tests pass |

Use the skill's `lint.mjs --app` and `inspect.mjs --app`, open every generated
fold/contact sheet, then critique and fix the worst visible problems. Explain valid
semantic category/technical mono exceptions. Zero automatic failures alone is not
completion. Do not discard color meanings or necessary borders to satisfy a style
warning. Record any intentional user-directed departures from stock skill tokens.

Required implementation checks: repository tests; backend unit/live read-only
integration tests if API/query/layout changes; TypeScript/production build; existing
and focused Playwright checks; a relevant offline CLI check; diff/privacy checks.
Store raw evidence in a new ignored `reports/runs/WORK-.../` directory. Report skips
and unavailable integrations accurately. Update app docs and normal work records;
record material implementation choices without rewriting finalized reviews.

Deliver changed-file summary, before/after screenshots and dimensions, actual test
results, quality provenance and remaining limits. Commit only the bounded task at
appropriate local checkpoints under repository instructions, preserving all prior
index contents; never use blanket staging or commit unrelated existing work. No
push, public publication or submission is part of this handoff.
