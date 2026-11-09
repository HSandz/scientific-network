# WORK-2026-11-09-006 — Final local PDF and submission package

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09T12:40:59.480817+07:00 (Asia/Bangkok) |
| Work performed | 2026-11-09 +07:00 |
| Contributor | Codex coordinator |
| Related task | WORK-2026-11-09-005 |
| Git state | main; report/source checkpoint `98bc295`; this new work entry remains outside that snapshot |

## Objective

Render/package the settled report and verify local delivery artifacts, privacy exclusions, member/source hashes and preservation of frozen inputs. No external delivery.

## Changes and findings

- Final artifacts are under `reports/runs/WORK-2026-11-09-006/package-v1/`: `report.pdf`, `report.html`, `scientific-network-submission.zip`, `submission-manifest.json` and renderer receipt. PDF is 19 A4 pages/six figures; ZIP is 63,305,524 bytes with 1,320 members.
- Tracked QA receipt: `reports/release-v3/local-package-receipt-v1.json`, with artifact/member hash references, numeric consistency, privacy/freeze verification and actual limitations.
- Source checkpoint is `98bc295d75e1fefd6bfcb04adef03a7e0e81cafe`. Its permitted tracked working-tree bytes are bound individually in the manifest. Fourteen historical CSVs differ from commit blobs only by CRLF/LF normalization; both hash representations are recorded, with frozen working bytes preserved. No other packaged source differences.
- Source snapshot predates this final receipt/work entry to avoid circular packaging; packaged status/logs therefore precede final verification. Embedded member manifest identifies actual bundle bytes. Final receipt is the post-package verification record, not an included member.
- Frozen graph, classifier, test/sample/packets, old receipts and figures remain unchanged. Agent quality gates fail at 88% precision; no post-audit graph fix or classifier tuning.

## Verification

| Command/check | Outcome | Evidence |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report` | exit 0; 81 packages resolved, 37 audited; no model download | actual locked environment |
| `uv run pytest` | exit 0; **419 passed/1 existing empty-parameterization skip**, 21.73s | ignored WORK-006/pytest-final.log |
| `uv run research-network schema` | exit 0 | ignored WORK-006/schema-final.json |
| `uv run --extra report python -m scientific_network.reporting.release_package --report reports/final-report/report.md --output-dir reports/runs/WORK-2026-11-09-006/package-v1` | exit 0; 19 A4 pages, six raster figures, 13 H1/H2 headings; all local report references included; no local-file annotations | renderer package receipt/manifest |
| `uv run --extra analysis --extra report python reports/runs/WORK-2026-11-09-006/verify-package.py` | exit 0; ZIP CRC/all member hashes pass; 89 frozen/completed file hashes match; all numeric table rows match JSON; two actual configured secret values checked, zero matches | small tracked QA receipt; diagnostic script ignored |
| Text/font/layout | final HTML and extracted PDF text equal inspected preview; all report text glyphs covered; zero replacements; final pages 15–16 visually inspected at 1600px | final quality-page PNGs and prior 16-page contact sheet; figures/tables/code visible without clipping |
| Read-only `git ls-remote --heads --tags origin` | exit 0; remote main `05ac5d83922c54bd006034e5c7296de00e811f72`, no tags | no push/tag |
| Ignore/exclusion checks | PDF/HTML/ZIP/run files ignored; no raw/interim/processed inputs, models, volumes, symlinks or configured secrets in bundle; explicit report PDF only | member manifest and Git ignore checks |

ZIP SHA256: `e67a76b3ab60240d1f7122bb73fb717cd69d192cd30b53e313253316835ce80c`.
No new source/roster/rights audits or graph reload were run. Six integrity queries and database inventory were freshly checked in WORK-004; idempotent replay remains the earlier checkpoint result. Eight report DOI links passed in WORK-004; GitHub HTTP504 remains not_verified. No new implementation or final-check failures in this checkpoint.

## Decisions

Preserve all frozen artifacts and failed AI quality gates. No graph reload/rebuild, threshold tuning or external write.

## Open issues and limitations

Real human identities/IDs/contributions, lecturer access/course AI-use rules and separately authorized delivery remain pending. Human annotation is optional.

## Next step

Supply real team/course/access facts for a new versioned render, then explicitly authorize desired remote delivery. Any identifier-handling correction is a separate graph version and new audit; preserve these failed outcomes. No independent local checkpoint remains unfinished.

## Corrections

None.

Finalized: 2026-11-09 12:44 +07:00.
