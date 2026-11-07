# WORK-2026-11-08-021 — P01 ACM Multimedia 2024 browser source review

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-08 00:50 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-017](2026-11-07-017-p01-acmmm-2024-source-closure.md) |
| Git state | `main` at `66e692d`; extensive existing uncommitted work preserved; no commit or repository push |

## Objective

Continue P01 with a bounded recheck of ACM Multimedia 2024 using the connected
browser route. Determine whether official source evidence closes the 1,149-ID
versus 1,150-acceptance discrepancy, track scope, and proceedings membership.
Preserve roster v10 and every frozen assignment unless complete permitted evidence
supports a new roster version.

## Changes and findings

- Added [D038](../decisions.md#d038--acm-multimedia-2024-browser-source-follow-up-2026-11-08),
  [source-correction overlay v11](../../data/manifests/five-year-source-corrections-v11.json),
  [source triage](../five-year-source-triage.md#acm-multimedia-2024-browser-source-follow-up-work-021),
  the current [completion-plan checkpoint](../pregraph-completion-plan.md), and
  aggregate-only [Report update](../../reports/site-report.md). No per-record IDs
  or paper metadata were added to tracked files.
- The connected browser recaptured the official accepted-ID text response (HTTP
  200; decoded body 5,497 bytes; 1,149 unique IDs). Its SHA-256 exactly matches
  WORK-017: `00441e7cd5f52a8030d6b5d316c66bae7707021fddb2a3647c3dd1e0d2c25fc2`.
  The response and headers are retained in ignored `reports/runs/WORK-2026-11-08-021/`.
- The official regular-paper page rendered in the connected browser says there is
  no long/short distinction and varying lengths receive the same review process.
  Its captured origin HTML remains a 7,508-byte JavaScript shell with no roster
  rows. The official BNI call says accepted papers appear as full papers in the
  main proceedings, with a separate review committee and criteria.
- A MarkItDown conversion of the official full-program URL yielded only 63 unique
  explicit `Paper <id>` labels. This is a partial converted view, not a hash-bound
  PDF capture or accepted-to-proceedings crosswalk. The aggregate result is in
  `reports/runs/WORK-2026-11-08-021/acmmm2024_program_route_audit.json`.
- The official research-track statistic remains 1,150 acceptances. The ID file,
  partial program route and rendered calls do not resolve the one-record mismatch
  or establish a complete accepted-paper roster. Bulk metadata reuse terms remain
  unverified. ACM Multimedia 2024 stays `access_unavailable` in roster v10 under
  D038; no v11 roster was created.
- The user reports one reviewer and unknown hours, with no second independent
  reviewer confirmed. P02 remains no-go for broader enrichment. No split,
  enrichment, paper PDF acquisition, graph or database operation occurred.
- The public Site is active/public at v18 with the existing project ID, URL and
  audience. The supported helper failed before checkout. The local Report update
  is not live.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Repository instructions, current handoff, completion plan, source triage/policy, v10 config and relevant work logs | completed | `AGENTS.md`, `README.md`, `docs/project-plan.md`, `docs/graph-schema.md`, `docs/status.md`, `docs/work-log/README.md`, `docs/pregraph-completion-plan.md`, `docs/five-year-source-triage.md`, `docs/source-policy.md`, `configs/corpus-five-year-v10.yaml`, WORK-017 and WORK-020 |
| Connected-browser GET of `https://2024.acmmm.org/files/accepted_papers.txt` | passed; HTTP 200, Brotli response decoded to 5,497 bytes; 1,149 unique numeric IDs; body hash matches prior capture | `reports/runs/WORK-2026-11-08-021/acmmm2024_accepted_papers.browser-decoded.txt`; SHA-256 above; rendered response-header hash in source corrections v11 |
| Connected-browser GET of `https://2024.acmmm.org/regular-papers` | passed; HTTP 200, 7,508-byte JavaScript shell; SHA-256 `24131a90c6f898357a100157e932bbc6e8d2c0651c6075207bcad09e71eae544`; rendered page states length-neutral regular-paper review | `reports/runs/WORK-2026-11-08-021/acmmm2024_regular_papers.html` and `.headers` |
| MarkItDown conversion of official full-program PDF and aggregate Paper-ID parse | conversion returned text; diagnostic found 63 explicit unique IDs, 60 also in accepted-ID file and 3 outside; partial only | `reports/runs/WORK-2026-11-08-021/acmmm2024_program_route_audit.json`; origin PDF bytes/hash not captured |
| Official BNI call route review | rendered call says accepted papers are full papers in main proceedings and uses a separate review committee and criteria | `https://2024.acmmm.org/files/MM24_BNI.pdf`; rendered source only, no local origin-PDF hash |
| Local `curl` recapture of accepted-ID file | failed, curl exit 6, HTTP 000; local DNS did not resolve `2024.acmmm.org` | no response artifact was returned |
| `python3 -m json.tool data/manifests/five-year-source-corrections-v11.json` | passed, exit 0 | JSON syntax valid |
| Read-only roster/split hash audit using `data/manifests/five-year-roster-v10/summary.json`, `data/manifests/five-year-splits-v1/inputs.json` and `summary.json` | passed, exit 0; 42/42 v10 output hashes, 7/7 split-input hashes, 76,629 membership rows/hash and 1,095 reserved tests verified; v11 inherited correction and v10 config bindings match | local Python hash check; summaries under `data/manifests/five-year-roster-v10/` and `data/manifests/five-year-splits-v1/` |
| Sites `get_site` for existing project | passed; active/public, version 18, existing project ID and URL retained | project `appgprj_6ae7698b8b2881919d49df2426c517a2` |
| Supported Sites source helper with fresh authorized credential | failed, exit 1, `Unable to prepare the Site.`; no checkout/source result returned | No source audit, push, build or publication; Site remains v18 |
| Python tests and roster replay | not run; documentation/source audit only, no project code or roster output changed | No new executable code or roster version |

## Decisions

[D038](../decisions.md#d038--acm-multimedia-2024-browser-source-follow-up-2026-11-08)
retains the unavailable disposition. D035's original hold and all scope, track,
threshold, and frozen-assignment rules remain in force.

## Open issues and limitations

The official 1,149-ID file still differs from the 1,150 research-track statistic.
The converted program view is partial and not a captured/hash-bound origin PDF;
no full proceedings reconciliation or metadata reuse authorization was found.
The source helper cannot prepare a Site checkout, so the local Report refresh is
not live. P01 still has 62 incomplete candidates; P02 remains no-go because
actual review capacity is not established.

## Next step

Continue P01 with another permitted official roster route from
[the completion plan](../pregraph-completion-plan.md). Reopen ACM Multimedia 2024
only if a complete official accepted-to-proceedings reconciliation and source-use
basis become available. Keep v10 and all frozen assignments unchanged; do not
begin broader enrichment while P02 is no-go.

## Corrections

None.
