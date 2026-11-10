# WORK-2026-11-09-019 — Redesigned Explorer follow-up review

| Field | Value |
| --- | --- |
| Status | completed (review only; findings open) |
| Recorded | 2026-11-09 23:55 +07:00 (Asia/Bangkok) |
| Work performed | 9 November 2026 |
| Contributor | Codex |
| Related task | WORK-017, WORK-018 |
| Git state | main at a2f8df6; prior staged/unstaged redesign and review changes preserved |

## Objective

Review the redesigned Research Explorer with design-taste-frontend; compare with the initial review and check dark/light themes and responsive usability. No application implementation.

## Changes and findings

Created [follow-up critique](../../reports/research-explorer-redesign-review-2026-11-09.md).
The redesign improves dark/light styling, desktop space, contextual details and
labels. Remaining findings: conflicting quality counts/targets, overlapping graph
nodes and weak relationship visibility, phone/control density and cramped 1024px
selection, modal/picker keyboard failures, accent-sensitive search, and different
development versus production CSS. No application/dependency/data edits.
Evidence: `reports/runs/WORK-2026-11-09-019/` (ignored).

## Verification

- `uv sync --locked --group dev --extra analysis --extra report`: exit 0.
- `uv run pytest`: exit 0; 508 passed, 1 existing empty-parameter skip, 24.67s.
- `npm --prefix apps/research-explorer/frontend run build`: exit 0; Vite >500kB
  chunk warning, 1.54MB raw / 476kB gzip JS; performance not benchmarked.
- Skill `inspect.mjs --app`: production `:4173` exit 0, 0 FAIL/0 WARN;
  development `:5173` exit 0, 0 FAIL/2 WARN (dev server and unloaded mono font).
- Skill `lint.mjs --app` on frontend source: exit 0, 0 FAIL/36 mono warnings;
  technical IDs/hashes/code are valid app-screen uses.
- Existing Playwright E2E against `:4173`: exit 0, 4 passed in 23.0s.
- Supplemental screenshot run: exit 0, 22 images, no console/page errors;
  all captures and both sets of three-width inspector sheets opened. Focused
  responsive/keyboard/search checks and settled-theme/lower-chart captures exit 0.
- Table and inspector both show Warut with 58 DB incident edges. Light preference
  survives reload. Manual failures are recorded in the report despite passing E2E.
- `git diff --check`: exit 0. Tracked app/dependency diff matches initial snapshot
  byte-for-byte (`cmp`, exit 0). Prior changes preserved; no staging/commit/push.

## Decisions

Retain the redesign direction. Recommend correcting display facts, graph legibility,
responsive composition and keyboard behavior before another visual restyle.
No new durable project/graph decision.

## Open issues and limitations

Findings remain unfixed by design. Local Chromium only; focused keyboard checks
are not a full accessibility audit. Development CSS mismatch cause unconfirmed.
No graph/scientific re-evaluation, performance benchmark or publication performed.

## Next step

Use the follow-up report to scope a separate implementation task; start with shared
quality facts and targets, then graph layout and responsive/keyboard behavior.

## Corrections

None.
