# WORK-2026-11-07-012 — Pregraph source and Site follow-up

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 20:41 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-011](2026-11-07-011-acm-siam-source-route-review.md) |
| Git state | main at 66e692d; extensive pre-existing uncommitted work preserved |

## Objective

Continue the completion plan from P01 using permitted official evidence, preserve
roster v10 and all protected assignments, and refresh the existing public Site
only after its exact source is audited and packaged. The user explicitly approved
using a short-lived repository write credential through the supported Sites
helper for the audited source and current Site publication.

## Changes and findings

- The official CIKM 2025 accepted-paper page and conference-hosted proceedings
  page were inspected through the Search connector. The rendered proceedings page
  separates Full Research, Short Research, Applied Research, Resource, Demo and
  PhD Symposium sessions, with article links into ACM Digital Library. This is a
  useful route/categorization lead, not a locally captured or hash-bound roster;
  no inclusion decision for the separately named Applied Research track was made.
- Sites confirmed the existing project is active and public at version 18. After
  the user's explicit authorization, the short-lived write credential was supplied
  only to the supported helper over hidden stdin. The first invocation from a
  nonempty `/tmp` failed generically. Following the documented empty-directory
  workflow, the retry failed before checkout because `git.chatgpt-team.site` did
  not resolve. No Site source was audited or built, and no push or deployment
  occurred. The credential was not written to disk or recorded here.
- Reverified all 42 output hashes in the v10 roster summary. Counts remain 98
  eligible, 10 verified no-edition, 22 unresolved and 40 access-unavailable;
  76,629 assignments and 1,095 protected tests remain guarded. No roster, config,
  split, enrichment, PDF, graph or database artifact changed.
- Updated this entry, the source triage, completion-plan checkpoint, status,
  work-log index and local Site Report. The public Site remains v18 because its
  source could not be opened.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `git diff --check` | passed (0), including after documentation updates | Worktree whitespace check |
| v10 roster hash audit | passed; 42/42 hashes match; 98/10/22/40 edition statuses and 76,629/1,095 frozen counts unchanged | `data/manifests/five-year-roster-v10/summary.json` and output files |
| Sites `get_site` | passed; existing project active, public, version 18, unchanged title/slug/URL | Project ID and state match the v18 receipt in `docs/reference/sites-iclr-access-retry-publication-2026-11-07.json` |
| Sites source helper | failed; exit 1 from initial misplaced attempt, then exit 128 in the documented empty directory: Git host DNS resolution failed before checkout | Supported helper; no direct Git or escalated fallback |
| CIKM 2025 official route review | route lead found; accepted and proceedings pages expose separate track categories, but no local raw capture or complete reconciliation | Search connector views of `cikm2025.org/program/accepted-papers` and `/program/proceedings` |
| `uv run pytest` / offline CLI | not run; this iteration changed documentation only and did not alter code paths | Not requested; no implementation check claimed |

## Decisions

None. Existing scope and evidence rules remain in force.

## Open issues and limitations

P01 remains failed with 62 incomplete candidates. A Search-rendered official page
does not satisfy the local hash-bound source requirement. The Sites source remains
unavailable because its Git host does not resolve in the supported helper. No
publication receipt or new Site version exists; the public Site remains v18.
Preserve all existing uncommitted changes and all protected assignments.

## Next step

When the managed DNS route to `git.chatgpt-team.site` and official conference
hosts is available, reopen the same Site source through the supported helper and
capture CIKM 2025's official accepted/proceedings pages locally before any new
roster version. Reconcile eligible tracks and rights, then continue with ACM MM
2024's official ID file.

## Corrections

None.
