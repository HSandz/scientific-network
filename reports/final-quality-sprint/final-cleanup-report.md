# Final cleanup and submission readiness — 11 November 2026

## Changes

- Human review criteria now distinguish a source-consistent relationship from an
  independently verified relationship. An official byline and OpenAlex ID alone
  do not verify real-person identity; dependent derived relations inherit identity
  uncertainty. The existing answer vocabulary and CSV schema remain unchanged.
- Both reviewer packets include every edge in `issues.json` in a separate flagged
  section. The 80-edge frozen sample, prespecified 20 random IDs and six risk cases
  are unchanged. Flagged overlaps retain their tags; AI concerns are held in
  separate post-blind pages. No human answers were supplied.
- The report retains historical v3 and current v4 measurements with explicit
  AI-assessed qualifications, denominators, figures, limitations and a checklist
  for missing team/course details.

## Validation

The clean source checkpoint `f3b00d412769c2a9eff9063b7702412cffe1e700` passes the
full Python suite (**644 passed, 1 existing skip**), frontend production build,
Playwright contracts (**8 passed**) and selected browser regressions (**37 passed**).
Frozen v4 structural validation passes with zero errors across all ten relations;
it does not measure semantic accuracy. Hashes for the graph, retained works,
frozen edge sample and issue ledger match their recorded values. The report renderer
validated 52 local links and embedded ten figures; the 28-page A4 PDF has no
replacement glyphs and its final checklist page was inspected.

Read-only checks of the public Explorer confirmed the live Analytics bundle exposes
the topic-assigned count, labeled denominator, all-paper denominator, coverage,
and identity-sensitivity note. Its deployed source commit is not exposed. No
deployment, graph/API change, push or submission occurred.

## Local package

The clean-checkpoint package is under the ignored run directory
`reports/runs/WORK-2026-11-11-008/package-v1/`:

- [Rendered report PDF](../runs/WORK-2026-11-11-008/package-v1/report.pdf) — 28 A4 pages.
- [Portable report HTML](../runs/WORK-2026-11-11-008/package-v1/report.html).
- [Source and report ZIP](../runs/WORK-2026-11-11-008/package-v1/scientific-network-submission.zip) — 1,754 members, including the rendered PDF.
- [Manifest](../runs/WORK-2026-11-11-008/package-v1/submission-manifest.json).
- [SHA-256 and validation receipt](final-cleanup-package-receipt.json).

The package excludes raw/intermediate/processed data, local credentials, temporary
run outputs and uncommitted Task2D work. Human validation remains **not performed**;
the Luna judgments remain AI assessments and do not establish verified course
accuracy.

## Team actions still needed

- Supply official names and student IDs for both members and their actual
  contribution summaries.
- Confirm exact course title/identifier, required advisor or instructor details,
  lecturer access requirements, and the course's AI-use disclosure wording.
- Confirm the submission destination and date. Render a new version if supplied
  details must appear in the report.
- Optionally complete and return the two human packets. Human annotation is not a
  prerequisite for the feasible work completed here.
- Separately authorize any future push, Pages deployment or external submission.
