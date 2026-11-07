# Official source correction v6 — ICAPS 2025

**Recorded:** 7 November 2026, Asia/Bangkok (UTC+07:00)  
**Method:** `five-year-official-rosters-v6`  
**Configuration:** [`corpus-five-year-v6.yaml`](../configs/corpus-five-year-v6.yaml)  
**Correction evidence:** [`five-year-source-corrections-v4.json`](../data/manifests/five-year-source-corrections-v4.json)

This roster-only revision resolves the ICAPS 2025 source-track ambiguity using the
official conference call and accepted-paper list. It leaves v1–v5, historical
reviews, frozen memberships, source/cache inputs, scope, graph schema, and quality
targets unchanged. It performs no enrichment, split creation, identity resolution,
service check, graph construction, or import.

## Measured roster

| Measure | v6 result |
| --- | ---: |
| Venue-year candidates retained | 170 |
| Eligible editions | 89 |
| Unresolved editions | 41 |
| Unavailable editions | 40 |
| Edition gaps | 81 |
| Roster observations | 88,608 |
| Included | 85,850 |
| Excluded | 2,758 |
| Record-level review | 0 |
| Frozen assignments guarded | 76,629 |
| Protected test assignments | 1,095 |

The total includes 160 edition observations inherited unchanged from the v2
baseline; ten AAAI/ICAPS editions were reprocessed under the v6 source method.
Inherited statuses retain their earlier evidence dates. These counts are roster
observations, not deduplicated works, graph nodes, or accepted edges.

## ICAPS 2025 evidence and disposition

The OJS issue contains 52 records: 48 accepted main-research records, three
accepted position papers, and one frontmatter record. The official [main technical
call](https://icaps25.icaps-conference.org/calls/main_track/) places theoretical,
algorithmic, modelling, position, and tools submissions under its main technical
call. The official [organization policy](https://icaps25.icaps-conference.org/organisation/roles_and_guidelines/)
states ICAPS 2025 uses topic classifications rather than tracks. The official
[accepted-paper page](https://icaps25.icaps-conference.org/program/accepted/)
contained 56 link occurrences and 51 unique OJS article IDs. The 48 OJS records
previously in review match 48 accepted IDs exactly and are now included. Three
position records remain excluded under the existing project rule for main archival
research papers; frontmatter remains excluded.

The OJS issue response is bound to SHA-256
`0a695196a6c0c21b31b1fc7157932c34e90f4c0d2b431b8af14cbf02923ea016`; the v5
edition roster hash is preserved in the correction manifest. The accepted-page
hash is for a captured browser DOM link extraction, not the raw webpage response.

## Reproduction and checks

The new v6 discovery replay ran with `httpx.Client.get` replaced by a function that
raises, so any uncached source access would have failed. It completed with zero
SourceCache network requests. The command returned **exit 1 as designed** because
81 edition gaps remain; the partial roster and ledger are preserved under the
ignored `data/manifests/five-year-roster-v6/` directory. The output summary records
zero new splits, zero canonical merges, and no enrichment or graph authorization.

The v6 configuration SHA-256 is
`a9ef4054daadb12ba63037cb9ec8e15eec35724db73af7f7a7d61774c900875d`. The manifest
and edition-ledger hashes are recorded in
[`five-year-source-recovery-v6.metrics.json`](five-year-source-recovery-v6.metrics.json).
The new 170-row CSV is [`five-year-edition-ledger-v6.csv`](five-year-edition-ledger-v6.csv).

## Remaining limits

P01 remains incomplete: the other 81 edition gaps and full main-roster coverage are
unresolved. ICLR, MICCAI, and AAMAS official route leads are recorded in
[`five-year-source-triage.md`](../docs/five-year-source-triage.md); those routes
have not yet produced complete eligible rosters. The preserved diagnostics and
pregraph freeze remain bound to their original v2 inputs and are not refreshed by
this roster version. Independent semantic quality and full pregraph readiness
remain unmeasured/false.
