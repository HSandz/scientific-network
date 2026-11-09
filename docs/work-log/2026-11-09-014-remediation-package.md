# WORK-2026-11-09-014 — Corrected report and local package

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09T18:19:35+07:00 (Asia/Bangkok) |
| Work performed | 9 November 2026 |
| Contributor | Codex coordinator and report/computation context |
| Related task | WORK-011–013; remediation E |
| Git state | main after85b6ead; report/README draft updates in progress |

## Objective

Integrate corrected measured graph/analysis and actual prospective audit, preserve failed history and unchanged topic limitations; build/check new local PDF/HTML/ZIP from a committed source checkpoint.

## Changes and findings

Report/README updated for current graph, before/after findings, exact coverage denominators and the failed80% affiliation target. New audit is complete:193/200 (96.5%), Wilson95%92.95–98.29%, AI-only numeric pass; topic/coverage failures and historical88% remain visible. Old report source preserved by Git and original ignored PDF/HTML/ZIP bytes retained. Personal facts remain pending.

## Verification

Locked `uv sync --locked --group dev --extra analysis --extra report` exit0; `uv run pytest` exit0:504passed,1existing skip,27.24s. Logs in `reports/runs/WORK-2026-11-09-014/`. No code changes since that suite. Draft numeric-table, local-link and figure-path checks pass. Bounded external HEAD checks:8DOIs reachable,GitHub404; actual lecturer/public access not_verified. Source checkpoint `8f0782ac3ce46a65ea1c1eb32c489fba2f980f85` committed before rendering. Renderer exit0:23 A4 pages,6figures,13section headings; text/font/glyph/local-file-annotation checks pass. Independent final verifier `uv run python reports/runs/WORK-2026-11-09-014/verify-package-v4c.py` exit0: ZIPCRC,1394members/1393manifest rows,1391tracked sources (1377exact commit blobs plus14known historical CRLF-only CSV differences),35HTML links plus6embedded images,9source/render tables,6177PDFword bounds,4actual configured secret values/0hits,541freeze+32completion bindings,125historical hashes unchanged.

Initial QA `verify-package-v4.py` exit1 demanded exact commit blob bytes for historical CSVs; all14differences are identical to the prior package receipt, only CRLF, so preserved. `verify-package-v4b.py` exit1 assumed at least10tables; report actually has9, all preserved and matched against source. Final verifier uses the measured source count. No package/source bytes were altered to bypass these checks. Failures/logs retained. Visual contact-sheet review of pages1,8,10,11,12,15,16,17,18,22,23, plus pages16/18 individually at1700px: no clipping/overlap; all6figures visible, current and old failed tables readable. Representative review, not every pixel.

Artifacts in ignored `reports/runs/WORK-2026-11-09-014/package-v4/`: report.pdf SHA256 `8c406a2e7b2bd1b0468a6d39dc489634884e4902fe4f8a438a718dc3bd1241a1`; report.html `d67e93782edf401421eb3716195221b2b777884e07a759c71f886081c9ea16ac`; ZIP `99a55fc62ab6d2158e76ea1907d44ad2750c1588e7b48eb34e1caaaeca5fea68`; manifest `3ea6492126d68dd03f690ea253c1c418a21165322ade41dcfd8fc816148ec639`. Full paths/sizes/hashes,14line-ending exceptions and QA are in tracked `reports/release-v4/local-package-receipt-v2.json`. That receipt and this final log/status follow the source snapshot and are intentionally not inside it.

## Decisions

No external delivery. Built a NEW ignored output directory after source commit; retained real failures and exposure limits. Finalized receipt/logs follow the archived source checkpoint; no recursive repackaging of the same package.

## Open issues and limitations

Real student names/IDs/contributions and lecturer AI-use/access facts unavailable. Package remains a local submission draft; no human validation or verified course accuracy.

## Next step

Authorized A–E complete. Supply real team/course facts from records before a separately versioned final delivery render; any push/tag/Site/invitation/submission needs separate authorization. No additional correction/tuning/audit cycle.

## Corrections

None.
