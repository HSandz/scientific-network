# WORK-2026-11-07-011 — ACM/SIAM official source-route review

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 20:27 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-010](2026-11-07-010-ieee-edition-route-review.md) |
| Git state | main at 66e692d; extensive pre-existing uncommitted work preserved |

## Objective

Continue P01 by checking official conference and proceedings routes for the 40
publisher-access-unavailable candidates, beginning with ACM and SIAM venues. Find
whether complete accepted main-research rosters, matching proceedings records,
track boundaries and lawful local handling can be established for any edition.
Preserve roster v10, every frozen assignment, and publisher restrictions unless
complete evidence supports a new versioned roster.

## Changes and findings

- The Search connector rendered official accepted-paper or program routes for
  selected years of KDD, The Web Conference, SIGIR, WSDM, RecSys, CIKM, ACM
  Multimedia and SIAM SDM. It exposed distinct research/applied/short/resource/
  industry/demo/Blue-Sky categories and KDD 2025's two submission cycles. These
  are route findings, not complete local source captures or proceedings joins.
- The Search-service view of the ACM Multimedia 2024 `accepted_papers.txt` file
  rendered 1,149 numeric lines; the official ACM MM statistics page reports 1,150
  accepted papers. The file was not retrieved locally, so its contents/count and
  any apparent difference remain unverified. Do not infer a missing paper or a
  roster count from the rendered excerpt.
- Local DNS failed for nine unique official publisher/conference hosts checked,
  including ACM MM 2024, CIKM 2025 and RecSys 2025. The Search connector returned
  403 Forbidden when opening the SIAM SDM 2025 proceedings DOI and the ACM Web
  Conference 2024 proceedings link. No restricted publisher path was retried or
  bypassed; no proceedings bytes were captured.
- Rechecked roster v10 integrity: all 42 files listed in its output hash map
  verify; the 170 edition rows still count 98 eligible, 10 verified no-edition,
  22 unresolved and 40 access-unavailable. The summary retains 94,857 roster
  observations, 91,355 included records, 76,629 guarded assignments and 1,095
  protected tests. This task changed no roster, config or split.
- No roster, edition disposition, config, split, enrichment input, paper PDF,
  graph or database artifact has been changed in this task.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Current status, P01 backlog, route triage, v10 ledger, and task-specific configuration | completed; P01 still has 40 publisher-access and 22 unresolved roster/adapter candidates; v10 remains current | `docs/status.md`, `docs/pregraph-completion-plan.md`, `docs/five-year-source-triage.md`, `reports/five-year-edition-ledger-v10.csv` |
| Official route search and page review | partial; accepted-paper/program routes and track boundaries identified for selected years in eight venue families; no edition closed | Search connector output is a route lead, not a local source capture; routes linked in `docs/five-year-source-triage.md` |
| Local DNS/HTTP probes | failed for nine unique official conference/publisher hosts with name-resolution errors; direct requests for the ACM MM file, CIKM accepted list and RecSys accepted-contributions page returned connection errors | Read-only `socket.getaddrinfo` and `requests.get` probes; no response body or file written |
| Publisher proceedings link checks through Search connector | blocked with 403 Forbidden for SIAM SDM 2025 and The Web Conference 2024 proceedings | Search connector responses; no retry or alternate access used |
| v10 roster integrity | passed; all 42 summary output hashes match; 170 edition rows remain 98 eligible / 10 verified no-edition / 22 unresolved / 40 access-unavailable | `data/manifests/five-year-roster-v10/summary.json`; `data/manifests/five-year-roster-v10/edition-ledger.jsonl` |
| Frozen-membership preservation | summary confirms 76,629 guarded assignments and 1,095 protected tests; no split/config path was written by this task | Current v10 summary and unchanged task input paths |

## Decisions

None. D022/D015 and the full-scope P01 gate remain in force.

## Open issues and limitations

Official accepted lists must be captured and reconciled to complete main-proceedings
frames. Search-indexed or connector-rendered page text is not a local hash-bound
source capture. Source reuse rights, track eligibility, source volume completeness
and local DNS/network access remain unresolved. No eligibility change is justified.

## Next step

After local DNS is restored, retrieve and hash the official conference-hosted
accepted-list sources, beginning with CIKM 2025's track-labeled accepted list and
ACM Multimedia 2024's small ID file. Resolve source terms and complete proceedings
crosswalks before producing any new version; preserve v10 and all frozen inputs.

## Corrections

None.
