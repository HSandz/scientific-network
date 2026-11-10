# Fresh-session prompt — implement Research Explorer improvements

```text
Work in /home/san/Code/scientific-network. Implement the Research Explorer
improvement plan in docs/research-explorer-improvement-plan.md. You have explicit
authorization to implement this bounded local-app task. Do not stop at another
review or plan, and do not ask routine permission to proceed.

Use $design-taste-frontend. Read:
/home/san/.agents/skills/design-taste-frontend/SKILL.md
and its references/app-screens.md in full. This is a working research app, so use
the app-screen workflow, not marketing-page rules. Retain the existing design
direction (achromatic-ledger, previous seed 103171675); use the new plan's softer
dark-mode requirements as the user's explicit palette override. Do not deal a
wholly different identity. If the skill path moved, locate it; don't silently skip
the requested skill.

At session start, in order, read AGENTS.md, docs/release-plan.md, docs/status.md
and the latest work-log entry. Then read:
- docs/research-explorer-improvement-plan.md (implementation specification)
- reports/research-explorer-redesign-review-2026-11-09.md (confirmed failures)
- apps/research-explorer/README.md and the affected source/tests/configuration.
Verify current files, Git state and runtime; logs and review counts are historical.
Create a new unused work-log entry using the repository template, with the actual
Asia/Bangkok date, and checkpoint meaningful progress as you work.

Context: React/TypeScript + Sigma.js + ECharts frontend :5173, FastAPI API :8000,
production preview :4173, read-only neo4j-five-year on Bolt :7689. Verify these
services before assuming they are running. Existing staged/unstaged app work and
an untracked EntityPicker.tsx may be present. Preserve all of it; do not reset or
overwrite prior work. Inspect nested instructions if present.

The user wants a comfortable research workbench and dislikes the current stark
black/white dark-mode contrast. Complete these outcomes:

1. Resolve development/build appearance parity and quality-display consistency.
   Analytics currently hardcodes affiliation counts unlike the release summary,
   and invents topic targets. Trace active summary/config/API values and use one
   structured quality contract across Analytics, Caveats, header and app docs.
   Current evidence to re-verify: 48,259/65,469 affiliation positions, 80% affiliation
   target, 80% topic coverage target, 95% topic-label precision target. Keep
   historical F1 separate from precision/coverage targets. Preserve all failures,
   AI-assessed provenance, confidence intervals and human-validation limitations.
   No invented F1 gate or fallback zeros/success when source data is unavailable.

2. Implement soft graphite dark mode across CSS AND Sigma/ECharts/native inputs:
   ground #1e1e1e, surface #252525, raised #2d2d2d, active #363636,
   main text #cecece, secondary #b0b0b0, metadata #9f9f9f,
   structural border #373737, grid #323232, control outline #5b5b5b,
   focus/data accent #7fa6cc. These are starting tokens; validate real rendering.
   Remove broad near-white buttons, stark hover labels and independent renderer
   whites. Keep neutral surfaces, readable semantic colors and the existing light
   theme. Text must remain >=4.5:1; essential focus/graphical states >=3:1. Do not
   dim connections into invisibility. Persist explicit theme, honor system choice
   when unset and avoid reload flashes. User preference outranks stock skill colors.

3. Fix responsive composition: one compact mobile navigation area, one graph
   control row, secondary tools in sheets/menus, compact expandable key. At 390x844
   aim for plot >=422px high beginning in the upper third, with 44px touch targets.
   Keep scope and a visible quality summary. Never leave a 360px graph between two
   fixed rails at 1024px; require >=600px remaining graph width for both rails.
   Give Analytics/Table their own wide layout, retain selected context for return,
   handle live resize without opening surprise drawers. Compact phone Analytics
   totals so the first chart enters the first screen; keep limitations accessible
   and visible. Use mobile table rows or a scroll frame with fixed identity column.

4. Make relationships readable in all four graph projections. Diagnose layout,
   node sizing, collisions and edge lengths together. Use deterministic display
   spacing/component placement, clear citation arrows and selected-neighborhood
   emphasis. Preserve labels on demand, full names and an accessible entity list.
   Retain node/edge membership, IDs, weights, evidence and metric scopes. Filters
   must be explicit and counted; no silent edge removal to make a prettier graph.
   Display layout changes are allowed; frozen network artifacts and scientific
   centrality/community calculations are not to be changed or rerun.

5. Complete interaction/accessibility: labelled modal semantics, initial focus,
   trapped Tab/Shift+Tab, inert background, topmost-layer Escape, focus restoration,
   proper combobox/listbox keyboard behavior and loading/error states. Switching
   picker presets/IDs must not retain a stale name. Make unaccented Tuomas Sandholm
   retrieve stored Tüomas Sandholm, preserving original spelling and stable IDs.
   Accent-tolerant retrieval must never merge same-name researchers. Keep requests
   bounded, debounced/cancelable and read-only, covering the full database rather
   than only displayed nodes. No new search service or database writes.

Implementation scope: apps/research-explorer/ and necessary work records. Read-only
API models, summary metadata, search and display-layout changes are allowed when
needed. Retain the stack and working features: all graph modes, expansion, search,
table pagination/sorting, analytics, Paths, Compare, exports, share state and source
evidence. No decorative imagery, marketing hero, framework replacement or unrelated
cleanup. Keep dependencies minimal; synchronize lockfiles for necessary changes.

Do not alter corpus/schema semantics, frozen graph/splits/audits/classifier/results,
release thresholds, pilot/extended databases, public Site or submission package.
Do not collect sources, rebuild/import graphs, retune, re-audit, publish, push or
submit anything. The app must continue to read only neo4j-five-year. Do not log
credentials/private source text. If a missing source is unavailable, report that
precisely and continue independent work.

Validation must prove behavior, not just appearance:
- Add focused regression checks for shared quality facts/targets, accent retrieval
  and distinct IDs, modal focus/picker keyboard behavior, drawer Escape, responsive
  selected state and theme persistence. Avoid tests that only mirror CSS tokens.
- Run uv sync --locked --group dev --extra analysis --extra report, then uv run
  pytest. Keeping report installed avoids optional Markdown skips from sync.
- Run PYTHONPATH=apps/research-explorer:src uv run pytest
  apps/research-explorer/backend/tests -v for affected API/query/layout paths;
  verify live Neo4j read-only integration when available. Report skips truthfully.
- Run a relevant offline CLI check (e.g. uv run research-network schema), frontend
  build and existing plus focused Playwright tests. Commands/config are in the app
  README; use PLAYWRIGHT_BASE_URL for testing both :5173 and fresh :4173.
- Inspect dark/light initial AND selected states at 390, 768, 1024, 1100, 1280 and
  1440px, all graph modes, evidence, Table/Analytics, modals and hover labels. Check
  resize without reload, no page overflow, actual plot dimensions and console errors.
- Use the skill's lint.mjs --app and inspect.mjs --app. Open every generated fold
  and contact sheet, critique the render and fix the worst remaining visual issues.
  Defend legitimate semantic graph hues and technical monospace exceptions; zero
  automatic failures is not sufficient. Fix any style-report false positives by
  documenting the scoped reason, not by destroying meaningful UI.

Keep raw screenshots/logs in a unique ignored reports/runs/WORK-.../ directory.
Update app documentation, the work log/index and docs/status.md (<60 lines).
Record material implementation choices per repository instructions, without
rewriting finalized review/history. Commit scoped work locally at required
checkpoints, preserving the pre-existing index and excluding unrelated changes;
no blanket git add or automatic commit of other agents' work. No push/publication.

Finish with a concise changed-file summary, before/after dark-mode and layout
evidence, actual checks/results, preserved scientific boundaries and remaining
limitations. Complete the implementation and verification in this session.
```
