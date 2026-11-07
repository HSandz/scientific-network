# WORK-2026-11-07-018 — P01 ICDM 2021 source closure

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 23:11 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-017](2026-11-07-017-p01-acmmm-2024-source-closure.md) |
| Git state | `main` at `66e692d`; extensive earlier uncommitted project work preserved |

## Objective

Continue P01 by checking whether ICDM 2021's official accepted-paper route can
produce a complete, permitted main-research roster and proceedings
reconciliation. Do not change roster v10, frozen assignments, track policy or
release thresholds without complete evidence.

## Changes and findings

- Captured official conference pages locally under the ignored
  `reports/runs/WORK-2026-11-07-018/` path. The accepted list contains **197
  unique IDs** (98 Regular Papers and 99 Short Papers); all 197 are present in
  the official conference schedule.
- The schedule has **239 unique DM IDs**. Its 42 additional IDs occur in
  separately named workshop events (40) and a PhD Panel event (2). The separate
  PhD Forum call describes doctoral submissions and IEEE proceedings, but does
  not establish a record-level link to the two panel items.
- The conference call states that accepted conference papers appear in IEEE
  Computer Society proceedings. A local IEEE Xplore proceedings request returned
  **HTTP 418**. Its command and response body were not retained; no bypass was
  attempted and no complete proceedings crosswalk was captured.
- The captured University copyright terms distinguish University-owned and
  third-party material. The conference pages do not establish ownership or bulk
  reuse permission for the accepted-paper metadata. ICDM 2021 therefore remains
  unresolved in v10; no v11 roster or source-correction overlay was created.
- Added [D036](../decisions.md#d036--icdm-2021-official-source-hold-2026-11-07),
  the source findings and capture hashes to [source triage](../five-year-source-triage.md#icdm-2021-official-accepted-list-follow-up-work-018),
  and this checkpoint to the [completion plan](../pregraph-completion-plan.md).
  Refreshed the local Report, status, roadmap and work-log index.
- V10 remains at **98 eligible / 10 verified no-edition / 22 unresolved / 40
  access-unavailable editions** and **94,857 observations** (91,355 included;
  3,502 excluded). P01 retains 62 incomplete candidates. All **76,629 frozen
  assignments**, including **1,095 tests**, remain protected.
- P02 remains **no-go**: one reviewer is reported, exact hours are unknown, and
  a second independent reviewer is unconfirmed. No split, enrichment, paper PDF,
  graph or database operation occurred.
- The existing public Site was read through Sites and is still active/public at
  v18 with its original project ID and URL. `getent ahosts git.chatgpt-team.site`
  exited 2 with no result, so no credential was requested and the local Report
  refresh remains unpublished.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Parse the captured accepted page and schedule with BeautifulSoup and compare unique `DM` IDs | passed, exit 0; 197 accepted IDs, 239 schedule IDs, all 197 accepted IDs present, 42 schedule-only IDs | Ignored capture directory; aggregate results in [source triage](../five-year-source-triage.md#icdm-2021-official-accepted-list-follow-up-work-018) |
| Group schedule-only IDs by their official calendar event | passed, exit 0; 40 in named workshop events and 2 in a separate PhD Panel event | Ignored `icdm2021-schedule.html`; aggregate only is published |
| Hash five captured official source pages with SHA-256 | passed, exit 0; hashes and byte counts recorded in source triage | `reports/runs/WORK-2026-11-07-018/` |
| `git check-ignore -v reports/runs/WORK-2026-11-07-018/*` | passed, exit 0; all raw captures are ignored | `.gitignore` rule for `reports/runs/**` |
| Direct local IEEE Xplore proceedings request | failed with HTTP 418; exact command/response body not retained; no bypass attempted | Limitation recorded above and in D036 |
| `getent ahosts git.chatgpt-team.site` | failed, exit 2; no DNS result | Supported Sites helper host remains unresolved |
| Sites `get_site` for project `appgprj_6ae7698b8b2881919d49df2426c517a2` | passed; active, public, v18, same URL and project ID | Sites response, sanitized; no credential requested |
| `uv run pytest` and roster replay | not run; this iteration changed documentation only; v10 outputs and frozen assignments were not rewritten | WORK-017 contains the prior fresh hash verification; no code or roster output changed in WORK-018 |

## Decisions

See [D036](../decisions.md#d036--icdm-2021-official-source-hold-2026-11-07). V10,
the existing track policy, frozen assignments and the P02 stop remain in force.

## Open issues and limitations

The accepted list and schedule establish the conference's 197 accepted IDs and
separate the 42 schedule-only items by event type, but the full IEEE proceedings
crosswalk and rights to reuse this metadata are unresolved. The two PhD Panel
items are not individually mapped to the separate PhD Forum call. The local
Report refresh is not live because the supported Sites Git host does not resolve.
P01 remains incomplete and P02 remains no-go.

## Next step

Continue P01 from v10 using complete, permitted official rosters. Revisit ICDM
2021 only when the proceedings crosswalk and metadata reuse authorization can be
established through an accessible official route; do not bypass HTTP 418. Keep
the no-go on broader enrichment until P01, P02 and the remaining pregraph gates
are satisfied.

## Corrections

None.
