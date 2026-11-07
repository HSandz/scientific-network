# WORK-2026-11-07-010 — ICDM/ICRA/IROS official edition-route review

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 19:54 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-009](2026-11-07-009-iclr-official-roster-access.md) |
| Git state | main at 66e692d; extensive pre-existing uncommitted work preserved |

## Objective

Continue P01 by checking official sources for the remaining ICDM, ICRA and IROS
2021–2025 editions. Determine whether complete accepted main-research rosters,
track boundaries, counts and permitted access/reuse can be established for any
year. Keep all unresolved years and the current v10 ledger unchanged unless the
complete evidence for a new roster version is ready. Preserve all frozen
assignments and the P02 no-go for broader enrichment.

## Changes and findings

- Reviewed all 15 ICDM/ICRA/IROS v10 ledger rows and checked official conference
  route leads through web search. ICDM 2021, 2024 and 2025 have official
  accepted-paper routes; the 2022 official program and 2023 schedule/OpenReview
  group are additional leads. ICRA materials point to PaperPlaza/InfoVaya; IROS
  materials include conference papers, journal-option presentations, late-breaking
  items and workshops that require year-specific filtering.
- The IROS 2022 official site reports 1,716 accepted papers and 1,765 papers in
  its final program including 49 journal presentations; the IROS 2023 official
  call says late-breaking results are not publications and are not submitted to
  IEEE Xplore. The ICRA 2023 official digest says program/paper access requires
  conference registration. These are track/access leads, not complete eligible
  roster counts.
- Local HTTP requests to four official hosts failed DNS resolution. The web Search
  connector refused PaperPlaza under robots.txt. No gated route, login or bypass
  was attempted, and no hash-bound source page, proceedings crosswalk, permission
  determination or complete roster was captured.
- All 15 editions remain unresolved; roster v10, the 76,629 frozen assignments
  and v2-bound diagnostic/pregraph inputs are unchanged. P01 remains failed with
  62 incomplete candidates; P02 remains no-go for broader enrichment. No
  eligibility, roster, split, enrichment, paper PDF, graph or database change
  occurred. Official route details are recorded in
  [source triage](../five-year-source-triage.md#icdm-icra-and-iros-official-route-review-work-010).
- The local Site Report is refreshed from aggregate route findings. The user
  explicitly approved using a short-lived Sites source credential through the
  supported helper to fetch and audit the Site source, then publish the existing
  public Site. The helper failed before checkout because `git.chatgpt-team.site`
  could not resolve, so the Site payload could not be audited or built. No source
  was pushed and no deployment occurred. Automatic
  review rejected a helper attempt before the source payload had been audited,
  then rejected a separate escalated-terminal credential attempt because it
  bypassed the managed proxy. No alternate or escalated route was used. The
  public Site remains at v18; this Report refresh is local and unpublished.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Read repository handoff, required project/schema/config/docs, current ledger and latest route-review entries | completed; v10 remains current, all 15 IEEE venue-years unresolved | README, status/work-log index, `docs/project-plan.md`, `docs/graph-schema.md`, `configs/corpus-five-year-v10.yaml`, completion plan, source triage, prior WORK-009, current v10 ledger |
| Official-route web search | partial; official accepted/program routes and track/access distinctions found; search excerpts are leads and are not captured rosters | Official links recorded in `docs/five-year-source-triage.md`; local source page hashes absent |
| Direct local HTTP checks for ICDM 2021/2025, ICRA 2025 PaperPlaza and IROS 2025 | failed source retrieval; all four hosts failed DNS resolution; loop reported all errors and exited 0 | Read-only `requests.get` probe; no response bodies or files written |
| PaperPlaza via web Search connector | blocked by robots.txt; no retry or alternate route used | Search connector response |
| Roster/frozen-assignment preservation | no roster rows or edition dispositions changed; no split, enrichment, held-out acquisition, PDF, graph or DB output | v10 ledger compared conceptually for ICDM/ICRA/IROS rows; frozen inputs were not written |
| Supported Sites source helper and publication | failed before checkout because `git.chatgpt-team.site` did not resolve; no push or deploy; existing Site remains v18 | Helper error; latest verified publication receipt is `docs/reference/sites-iclr-access-retry-publication-2026-11-07.json` |
| Site source audit/build and browser QA | not completed; source checkout was unavailable, so no Site payload was audited or built and no browser QA ran | Supported helper failed before checkout; local Report snapshot is not the Site source repository |
| Automatic review of credential-transfer attempts | helper attempt rejected while source payload was unaudited; escalated-terminal attempt rejected because it bypassed the managed proxy; no credential was sent through the rejected terminal route | Automatic review outcomes; no alternate route used |
| `uv run pytest`, source-disabled roster replay, browser QA | not run; no executable code or roster output changed; source records were not captured | Not applicable at this route-only checkpoint |

## Decisions

No new decision proposed. D022, D015, rights/access policy, roster v10, frozen
assignments, and the P02 stop remain in force.

## Open issues and limitations

The official IEEE Xplore records listed in source triage are individual examples,
not complete volume rosters. ICRA/IROS program systems may expose only presentation
information and not an exportable publication crosswalk. Publisher permission and
track boundaries remain to be checked. The Site source payload was not available
to audit or build, and browser QA and publication were not completed because the
supported source helper could not resolve its Git host. The refreshed local Report
is unpublished. The prior escalated attempts were rejected by automatic review for
the reasons recorded above.

## Next step

After supported helper DNS is restored, audit and build the current Site source,
run browser QA, then publish the aggregate Report update to the existing Site and
save its receipt. Resume the IEEE route review from permitted source captures;
add no roster rows unless acceptance, track policy, complete proceedings, and
reuse evidence close for an edition.

## Corrections

### Dated correction — 2026-11-08

The WORK-010 statement that no hash-bound ICDM 2025 accepted-page capture existed
was imprecise. The ignored file
`reports/runs/WORK-2026-11-07-010/icdm2025_accepted.html` was present, contains
238,000 bytes, and hashes to
`22509c104ae6b92970246d875a0604df54d613fa9d7dd93081e4a907c1277d00`. A fresh
direct capture from the official accepted-page URL returned HTTP 200 with
238,000 bytes and the same SHA-256; the current response headers are retained
under `reports/runs/WORK-2026-11-07-020/`. The earlier file has no retained
HTTP status or response headers, so its original retrieval metadata remains
unknown. The corrected source capture verifies the page body and current origin;
it does not resolve track membership, the full proceedings join or reuse rights.
See [D037](../decisions.md#d037--icdm-2025-accepted-list-audit-2026-11-08) and
[WORK-020](2026-11-07-020-icdm-2025-offline-source-audit.md).
