# WORK-2026-11-07-003 — ICLR official source-route review

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 08:57 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-002](2026-11-07-002-aamas-roster-closure.md) |
| Git state | main at 66e692d; extensive prior uncommitted work preserved |

## Objective

Continue P01 from [the pregraph completion plan](../pregraph-completion-plan.md)
by checking the official OpenReview route for ICLR 2021–2025: edition-group
identity, accepted-main-paper roster access/completeness, track boundaries, and
source-use terms. Do not change scope, frozen assignments, or the P02 no-enrichment
stop. Promote no edition without a complete, reconciled official roster.

## Changes and findings

- Started from roster v8; ICLR remains five unresolved edition candidates in the
  current source ledger. The current local plan identifies the OpenReview venue
  index and a prior 2025 API availability error as leads, not verified rosters.
- The official OpenReview venue index lists distinct conference groups for each
  target year; the official ICLR proceedings FAQ directs users to OpenReview for
  all accepted papers from 2013–2025. The separate current electronic-proceedings
  index lists ICLR 2024–2026.
- ICLR 2024's official proceedings book lists 2,260 papers, matching its official
  fact sheet's 2,260 accepted papers. ICLR 2025's book lists 3,703 papers, while
  the currently hosted draft fact sheet reports 3,704 accepted; that difference
  is unresolved. No count-based promotion was made.
- The ICLR FAQ says authors retain copyright and grant ICLR a publication license;
  this was not treated as clearance to republish this project's per-record roster.
- Local retrieval could not produce a hash-bound input: the OpenReview API request
  returned HTTP 403 (315-byte response), and the proceedings host failed local DNS
  resolution (curl exit 6). Search-service page views are not stored source captures.
  No ICLR roster rows, parser/config version, sample, enrichment request, PDF, or
  graph operation was produced.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Official OpenReview venue index, ICLR Proceedings FAQ and official year pages | confirmed routes for 2021–2025; conference groups are distinct from workshops/side tracks | OpenReview venue index; `https://iclr.cc/FAQ/Proceedings`; official proceedings pages |
| ICLR 2024/2025 proceedings-page and fact-sheet counts | 2024 count agrees (2,260); 2025 count differs (3,703 proceedings / 3,704 in hosted draft fact sheet), unresolved | official ICLR proceedings pages and fact sheets, linked in `docs/five-year-source-triage.md` |
| `curl -sS --max-time 15 --get --data-urlencode 'content.venue=ICLR.cc/2024/Conference' --data-urlencode 'limit=1' -o /dev/null -w 'HTTP %{http_code}; bytes %{size_download}\n' https://api2.openreview.net/notes` | curl exit 0, HTTP 403, 315-byte response | OpenReview API access check from repository environment |
| `curl -sS --max-time 30 -o /tmp/scientific-network-iclr-2024-book-WORK003.html -w 'HTTP %{http_code}; bytes %{size_download}\n' https://proceedings.iclr.cc/paper_files/paper/2024` | curl exit 6; local DNS resolution failed; no file retained | bounded access check; no roster or PDF downloaded |
| Complete accepted-roster retrieval and track reconciliation | not run; all five editions remain unresolved | Requires locally accessible complete official source and hash-bound capture |
| Frozen assignments / P02 boundary | preserved; no new collection action authorized by this entry | v8 ledger and D029/D031 |
| Documentation checks | pending | updated status, roadmap, source triage, local Report and work log |

## Decisions

None at task start. D022, D029, D031, the existing scope and D015 track policy,
all frozen assignments, and the P02 no-go remain in force.

## Open issues and limitations

ICLR's per-year accepted-paper roster for 2021–2023 has not been locally retrieved;
2025 has an unresolved count difference. Although the 2024 official count matches,
its full roster was not captured into a reproducible local artifact. Search
results and remote page views cannot prove local roster completeness.

## Next step

Resume P01 with another source family or retry ICLR only when an approved, usable
source route can produce complete hash-bound roster inputs. Keep all five ICLR
editions unresolved until per-year accepted-paper completeness and track scope
are reconciled. Do not add partial rows or change the frozen sample.

## Corrections

**2026-11-07 follow-up (WORK-004):** A later relative-link integrity check passed
across 13 updated project Markdown files, including this entry. The original
verification row remains accurate for WORK-003; this check does not change its
partial roster outcome or the ICLR access failures recorded above.
