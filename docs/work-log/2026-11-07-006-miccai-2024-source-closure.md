# WORK-2026-11-07-006 — MICCAI 2024 official source closure

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 10:14 +07:00 (Asia/Bangkok) |
| Finalized | 2026-11-07T18:05:20+07:00 |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-005](2026-11-07-005-aamas-2023-reconciliation.md) |
| Git state | main at 66e692d; extensive prior uncommitted work preserved |

## Objective

Continue P01 from roster v9 by reconciling MICCAI 2024's 856 Society accepted
records against the official Springer 12-volume main-proceedings set. Preserve
all historical inputs and frozen assignments, and keep broader enrichment and
graph construction stopped at the existing P02/P03 gates.

## Changes and findings

- Captured all 49 official Springer table-of-contents pages across the 12 MICCAI
  2024 main-proceedings volumes, plus the Society list and Springer series index.
  Captures remain in the ignored `reports/runs/WORK-2026-11-07-006/` directory.
- Reconciled 856 Society research records one-to-one to 856 distinct Springer
  chapters: 836 exact-title and 20 unique title-and-byline matches. The only
  additional Springer chapter is a correction notice tied to an already-listed
  paper, excluded as nonresearch. D033 makes the edition eligible under the
  existing track policy; no scope or threshold changed.
- Added the v10 source overlay/configuration, parser and reconciliation logic,
  focused tests, aggregate report/metrics, and 170-row ledger. V10 has 98 eligible
  editions, 22 unresolved roster/adapter editions, 10 no-edition findings and 40
  access-unavailable editions; 94,857 observations (91,355 included, 3,502
  excluded). The 62 incomplete candidates keep P01 partial.
- Preserved all 76,629 frozen assignments, including 1,095 tests. No new split,
  enrichment request, canonical merge, PDF download, graph write, or DB operation.
  P02 remains no-go for broader enrichment; diagnostics/pregraph remain v2-bound.
- Refreshed the native Site Report with v10 aggregates and historical v9 artifacts,
  preserving the existing Plan, native 399/533 historical explorer, project ID,
  URL and public audience. Published as Site version 15 after the user explicitly
  approved the short-lived source-credential handoff. The exact source commit,
  deployment and sanitized artifact hashes are in the [receipt](../reference/sites-source-recovery-publication-2026-11-07.json);
  Plan/Report text snapshots are preserved in docs/reference/.
- Static and browser QA passed for tab switching, plan search, relationship guide,
  factual graph filtering, mobile layout/navigation, downloads and zero console
  errors/warnings. One existing keyboard issue remains: Escape did not close the
  search dialog even though its hint says it should; the keyboard-accessible Close
  search button works. No unrelated UI change was made.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Required repository docs, current handoff, latest relevant entries, plan, source triage, v9 config/report/ledger, source policy, D015 and Git state | completed | `AGENTS.md`, `README.md`, `docs/project-plan.md`, `docs/graph-schema.md`, `docs/status.md`, `docs/work-log/README.md`, WORK-005, `docs/pregraph-completion-plan.md`, `docs/five-year-source-triage.md`, v9 artifacts, `docs/source-policy.md`, `docs/decisions.md` |
| `uv run research-network discover --config configs/corpus-five-year-v10.yaml --output /tmp/scientific-network-v10-fresh-2026-11-07 --cache /tmp/scientific-network-v10-no-network-cache` | expected exit 1; 98 eligible / 10 no-edition / 22 unresolved / 40 access-unavailable; 94,857 observations; 62 incomplete | Fresh isolated output in `/tmp/scientific-network-v10-fresh-2026-11-07`; stdout checkpoint in `reports/runs/WORK-2026-11-07-006/discovery-replay.json` |
| Fresh versus saved v10 summary and all declared output hashes | passed; summaries match exactly, all 42 hashes match in both trees | `data/manifests/five-year-roster-v10/summary.json`; isolated `/tmp` output |
| Inherited v9 edition-artifact comparison | passed; 36 common edition roster/summary hashes unchanged; v10 adds only MICCAI 2024 roster/summary among edition artifacts | v9/v10 `summary.json` `output_sha256` maps |
| `UV_CACHE_DIR=/tmp/uv-cache-work006 uv run pytest` | passed; 205 tests, including seven MICCAI 2024 parser/reconciliation cases | `tests/test_miccai2024_reconciliation.py` and full suite |
| V10 CSV and saved-output hash audit | passed; 170 ledger rows reconcile to 91,355 included, 3,502 excluded and zero review; all 42 saved hashes verify | `reports/five-year-edition-ledger-v10.csv`; `data/manifests/five-year-roster-v10/summary.json` |
| env PANDOC=/tmp/pandoc-sites-miccai-v10/pandoc-wrapper python3 build_site.py (Site checkout) | passed; 20 Plan sections / 2 tabs, 12,142 Plan words, 3,172 Report words | /tmp/sites-miccai-v10/.sites-checkout |
| python3 reports/runs/WORK-2026-11-07-006/site-static-audit.py /tmp/sites-miccai-v10/.sites-checkout | passed; 268 unique IDs, 20 sections, 22 downloads resolve, no duplicate IDs or iframe/object/embed; Plan download hash matches source; v10 aggregate and historical labels present | `reports/runs/WORK-2026-11-07-006/site-static-audit.json` |
| Local browser QA at http://127.0.0.1:8765/ | passed for Plan/Report tabs, search, relationship guide, report filter, mobile navigation and overflow; zero console errors/warnings. Limitation: Escape did not close the search dialog; Close search works with keyboard | `reports/runs/WORK-2026-11-07-006/site-browser-qa.json` |
| Sites publication | succeeded; version 15 deployed to the same public URL and audience; source commit `468ffd3795351e264ba0102dd887c3c68e3b5ab4` | sanitized receipt and Plan/Report snapshots |

The initial CLI attempt without `UV_CACHE_DIR` exited 2 because the default `/home/san/.cache/uv` is read-only. The successful rerun used `/tmp`. Discovery exited 1 by design while the 62 remaining edition candidates are incomplete. The first `git diff --check` reported intentional Markdown hard-break spaces in the new status line; they were removed and the check was rerun.

The first Site helper handoff was rejected by automatic review before its JSON
stdin was transmitted; no token was sent and no push occurred in that attempt.
After the user explicitly approved that specific transmission, a fresh credential
was sent only through the supported helper's hidden stdin. No credential was
saved. The helper pushed the audited source, packaged it and the Sites connector
saved/deployed the exact version.

## Decisions

[D033](../decisions.md#d033--miccai-2024-full-proceedings-reconciliation-2026-11-07) records the accepted-paper/chapter reconciliation and nonresearch correction exclusion. D022 and D029–D032, the 2021–2025 scope, D015 track policy, frozen assignments, and P02 no-enrichment stop remain in force.

## Open issues and limitations

P01 remains incomplete: 22 unresolved roster/adapter editions and 40 publisher-access candidates remain. This includes MICCAI 2022, AAMAS 2023, ICLR 2021–2025, ICDM/ICRA/IROS adapter gaps and restricted ACM-family editions. Roster reconciliation is not independent semantic evaluation. P02, prospective P03 sampling, broader enrichment, graph readiness and full pregraph completion remain unachieved. The Site's existing search-dialog Escape behavior remains a small QA issue.

## Next step

Continue P01 from `configs/corpus-five-year-v10.yaml` under new work entry WORK-007, using complete permitted official rosters and immutable outputs. Keep AAMAS 2023 unresolved absent complete identity/track evidence; preserve all frozen test IDs. Do not begin broader enrichment or graph construction while P02/P03 gates remain unmet. Reopen the Site keyboard issue only in a separately scoped update.

## Corrections

None.
