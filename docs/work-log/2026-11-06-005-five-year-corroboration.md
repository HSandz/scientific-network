# WORK-2026-11-06-005 — Reviewed source corrections and public identifier corroboration

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-06T21:58:05+07:00 |
| Work performed | 2026-11-06 (UTC+07:00) |
| Finalized | 2026-11-06T22:20:51+07:00 |
| Contributor | Codex |
| Related task | [WORK-2026-11-06-004](2026-11-06-004-five-year-headers.md) |
| Git state | main at 66e692d; prior uncommitted work preserved |

## Objective

Verify restored Docker services; implement input-bound printed-source corrections and conservative public-ORCID publication corroboration on the frozen development diagnostics. Preserve historical inputs/tests/graphs and all failures. No database writes in this iteration.

## Changes and findings

- Added D025, `configs/five-year-corroboration-v1.yaml`, five input/PDF-bound
  printed-source overlays and `resolve/diagnostics.py` / `corroborate-diagnostics`.
  Originals remain unchanged: one failed metadata record and two GROBID failures.
- 49/68 source-eligible papers (45 before overlays); 84 eligible ORCID responses;
  10 researchers (one known/nine new), 11 authorships over nine papers and one
  reviewed affiliation triple. Six DOI / five Unicode title+year corroborations.
- 345 mixed-unit review rows; public works absence, contradictory crosswalks,
  missing metadata and unreviewed printed mappings remain unresolved.
- No graph materialization/import, no new OpenAlex requests or PDF collection.
- Reports/workflow/roadmap/instructions/current handoff updated; Site publication
  completed as Site v12; [receipt](../reference/sites-corroboration-publication-2026-11-06.json).

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run pytest` | 145 passed, exit 0 | ignored run `pytest.log`; 15 new synthetic contract tests |
| `uv run research-network corroborate-diagnostics --help` | exit 0 | explicit path CLI available offline |
| Corroboration command in `docs/five-year-collection.md` | exit 1 for 345 review rows, all 68 checkpoints retained | `data/processed/five-year-corroborated-v1/summary.json` |
| Same command replay | exit 1, identical output hashes/summary | ignored run `corroborate-replay.log` |
| CLI replay with `SourceCache.get` raising on calls | exit 0 wrapper; CLI's expected 1 asserted; zero calls | ignored run `offline-replay.log` |
| Protected artifacts and raw evidence | 7,645 unchanged; 362 sources hash-verified; 84 new ORCID / zero OpenAlex response descriptors | ignored run `verification.json` |
| Read-only services before/after | GROBID alive, HTTP 200; both Neo4j HTTP 200; 154/211 and 399/533 unchanged | `services-before.json`, `verification.json` |
| Site opening | first attempt failed (`Unable to prepare the Site`); prior temporary checkout was absent; fresh empty checkout opened successfully | helper returned source `bc758ef0ca261521775288fdb3e4df2d4ba74822` |
| Site build/static checks | exit 0; 20 Plan sections, two tabs, 265 unique IDs, zero embeds; unchanged payload hash | ignored run `site-static-check.json` |
| Local browser QA | 390/1440px, tabs/keyboard, search, graph projection/reset and new downloads passed; zero console errors | ignored run `site-browser-check.json`; source-object count rechecked after expanded verification |
| Hosted browser verification | new counts/362 sources visible, 20 Plan sections, zero embeds in Plan/Report; aggregate download HTTP 200; one hosting-injected frame outside panels | same live URL |
| `git diff --check` | exit 0 | final repository whitespace check |
| Site source push/package/save/deploy | succeeded; v12, commit `de26a4f1c30b3808626e1d0bee7c35c7ea537ea2`; existing public audience/URL | [publication receipt](../reference/sites-corroboration-publication-2026-11-06.json) |

Source header SHA `ce769d553056e1e8c2ed43d49b513645ee4e364bc4de116092247b7d91cc832c`;
config SHA `f73dabb0570c04091798a1c50ff3eb087958289d7701e07c16e616719530ac49`;
review SHA `561301590f8af3f6174079cc2ba47127b349f97470400cd6bcf6f987075db8a2`.
Frozen membership/diagnostics/tests and output hashes are in the tracked aggregate
`reports/five-year-corroboration-v1.metrics.json`. Source responses, full metadata,
PDFs/support/queues and raw checks remain ignored. Graph versions unchanged.

## Decisions

[D025](../decisions.md#d025--reviewed-source-overlays-and-public-identifier-corroboration-2026-11-06).
No release gate, graph schema, corpus boundary or quality-threshold changes.

## Open issues and limitations

Independent accuracy/recall/F1 unmeasured. Global canonical works unresolved;
conservative ORCID and crosswalk policy limits coverage. Only reviewed printed
mappings can accept affiliations; one accepted triple is development evidence,
not an independent audit. RSS parser/OCR conversion itself remains unrepaired;
source review overlays do not change parser-success counts. No collection jobs
remain running. Local preview stopped during final teardown. Existing DBs/HTML/payloads untouched. Project Git remains uncommitted.

## Next step

Review remaining byline/crosswalk conflicts and printed author-affiliation mappings
in new versioned outputs, then reconcile canonical works and freeze accepted support
before isolated graph materialization. Preserve old/new tests and require resolvable
source evidence for every accepted support row.

## Corrections

None.
