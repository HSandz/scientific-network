# Submission-detail update

Status: complete. Recorded: 2026-11-12T08:21:18+07:00 (Asia/Bangkok).
Baseline: `1a89355`; scope: `report/latex/` only. Existing unrelated
identity-quality changes are preserved. Repository-wide journal/status writes
are superseded by the user's report-only boundary.

Updated `report-info.tex` with the exact user-supplied names and student IDs,
course code, bilingual faculty name, localized instructor credential (PhD/TS),
and date `12/11/2026`. No contribution details were supplied; those two fields
remain identifiable placeholders. README now describes the remaining fields.

Checks: `make -C report/latex all` and the report verifier completed with exit 0.
Both PDFs remain 23 pages. All pages were rendered again; both new covers were
visually inspected at 1800px, with intact Vietnamese names, clean layout and no
overflow. Extracted cover text matches every supplied value. Pages 2–23 of each
edition are pixel-identical to the previously inspected version at 100 dpi.
No scientific content, figure, source data or result changed. No repository-wide
tests or database checks were needed or run for this metadata edit.

Local records: `review/submission-details-2026-11-12/` contains build/verification
logs, full page renders/contact sheets, high-resolution covers, comparison
checks and the previous verification JSON. `REVIEW-BILINGUAL.md` has a dated
addendum with current PDF hashes; its original review remains historical.

Next: fill actual contributions if required, confirm the disclosure and arrange
lecturer repository access before final submission. No push or deployment.
