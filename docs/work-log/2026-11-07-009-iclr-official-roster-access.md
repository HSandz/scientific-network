# WORK-2026-11-07-009 — ICLR official roster access retry

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 19:40 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-008](2026-11-07-008-aamas-2023-followup.md); prior route review [WORK-2026-11-07-003](2026-11-07-003-iclr-source-review.md) |
| Git state | main at 66e692d; extensive pre-existing uncommitted work preserved |

## Objective

Continue P01 by retrying the identified official OpenReview API route for complete
ICLR Conference main-track rosters for 2021–2025. Retain all years as unresolved
unless complete, hash-bound evidence closes each roster and accepted track
boundary. Preserve roster v10, frozen assignments and the P02 no-go for broader
enrichment.

## Changes and findings

- Work opened from the prior official route/access review in WORK-003 and the
  current ICLR disposition in the v10 edition ledger.
- Official OpenReview v2 API documentation confirms that the notes endpoint
  supports invitation filters and pagination. The readable official ICLR 2024
  group metadata identifies `ICLR.cc/2024/Conference/-/Submission`.
- The first-page/count request for that official invitation returned HTTP 403
  `ChallengeRequiredError`. The conference browser page rendered its group shell
  without accepted-note content. A separate search endpoint returned zero, which
  is not an accepted-paper count. No challenge verification was attempted.
- No hash-bound roster was captured. All five ICLR years remain unresolved; no
  eligibility change or roster row was added. Roster v10 and all frozen
  assignments remain unchanged; P01 fails with 62 incomplete candidates, and
  P02 remains no-go for broader enrichment.
- Updated [source triage](../five-year-source-triage.md), the local
  [Site Report](../../reports/site-report.md), status and the work-log index.
  Published Site version 18 while preserving the existing project ID, URL,
  audience, full Plan and historical graph explorer; see the
  [receipt](../reference/sites-iclr-access-retry-publication-2026-11-07.json)
  and [Report snapshot](../reference/sites-iclr-access-retry-report-2026-11-07.md).

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Read current status, completion-plan backlog, ICLR source triage and WORK-003/008 | completed; ICLR 2021–2025 are unresolved; prior API returned HTTP 403 and proceedings retrieval failed DNS | `docs/status.md`, `docs/pregraph-completion-plan.md`, `docs/five-year-source-triage.md`, related work entries, v10 ledger |
| OpenReview documented endpoint research | passed; official API docs specify v2 note search and invitation filtering; official conference group metadata gives the `Submission` invitation | OpenReview official API docs and ICLR 2024 group page; search-service snapshots were not used as roster data |
| `curl -sS --max-time 20 -H 'Accept: application/json' -o /tmp/WORK-2026-11-07-009-iclr-group-2024.json -w 'HTTP %{http_code}; bytes %{size_download}\n' --get --data-urlencode 'id=ICLR.cc/2024/Conference' https://api2.openreview.net/groups` | HTTP 200; official group metadata response is 8,596 bytes; sanitized hash and invitation identifier recorded | `reports/runs/WORK-2026-11-07-009/openreview-route-audit.json` |
| `curl -sS --max-time 20 -H 'Accept: application/json' -o /tmp/WORK-2026-11-07-009-iclr-api-search-2024.json -w 'HTTP %{http_code}; bytes %{size_download}\n' 'https://api2.openreview.net/notes/search?term=ICLR.cc%2F2024%2FConference&content=venue&venue=ICLR.cc%2F2024%2FConference&limit=1&offset=0&count=true'` | HTTP 200; zero search matches; not treated as a roster count | Sanitized response hash in local route audit |
| `curl -sS --max-time 30 -H 'Accept: application/json' -o /tmp/WORK-2026-11-07-009-iclr-submissions-2024-page1.json -w 'HTTP %{http_code}; bytes %{size_download}\n' --get --data-urlencode 'invitation=ICLR.cc/2024/Conference/-/Submission' --data-urlencode 'limit=1' --data-urlencode 'offset=0' --data-urlencode 'count=true' https://api2.openreview.net/notes` | HTTP 403, 361-byte `ChallengeRequiredError`; roster retrieval stopped, no challenge attempted | Sanitized response hash in local route audit |
| Official ICLR browser shell | partial; page title/group metadata loaded but accepted-note content did not; console reported 8 errors and 21 warnings for that page session | Browser page check; no challenge or verification bypass attempted |
| `PANDOC=/tmp/scientific-network-pandoc-wrapper python3 build_site.py` in the v17 source checkout | passed, exit 0; 20 Plan sections, two tabs, 12,142 Plan words, 5,099 Report words, 1,242,097 HTML bytes | Site build for commit `adfdc8cbd7054adbdc3e466a82b4a3534c2beeff` |
| `.venv/bin/python reports/runs/WORK-2026-11-07-009/site_static_audit.py > reports/runs/WORK-2026-11-07-009/site-static-audit.json` | passed, exit 0; 276 unique IDs, 22/22 downloads resolve, no embedded documents, v10/frozen counts and historical 399/533 payload preserved | Local static audit JSON in ignored run directory |
| Supported Sites source helper, save/deploy and `get_site` | passed; source commit `adfdc8cbd7054adbdc3e466a82b4a3534c2beeff`; version 18 active/public at unchanged URL | `docs/reference/sites-iclr-access-retry-publication-2026-11-07.json`; local archive SHA-256 `75d3472cd0c5bbb6969e078068ef11e0ad6d3dc49670b0181245ae93a19fbc5d` |
| Live browser verification | passed after cache-busting query; Report tab, ICLR 403 blocker and non-roster interpretation visible; 20 Plan sections, zero embedded docs, zero console warnings/errors | Receipt browser QA section and ignored static audit |
| `uv run pytest` and roster replay | not run; no executable project or roster code/output changed | Scope was source access triage and documentation |

## Decisions

No new decision proposed. D022, D015 and all existing scope, track, test-protection
and enrichment boundaries remain in force.

## Open issues and limitations

No hash-bound complete ICLR roster is currently available in the repository. The
official notes endpoint now requires challenge verification from this route; a
route check or search result cannot replace the complete roster. All five ICLR
years therefore remain unresolved.

## Next step

Continue P01 with an unresolved official route that permits complete roster
verification, starting from the 21 adapter gaps across ICLR, MICCAI 2022, ICDM,
ICRA and IROS or the 40 publisher-access candidates listed in the completion plan.
Keep ICLR unresolved unless OpenReview provides an accessible official roster;
do not attempt challenge bypasses. Preserve v10 and all frozen assignments.

## Corrections

None.
