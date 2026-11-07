# WORK-2026-11-06-006 — Pregraph evidence closure and readiness freeze

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-06T22:29:56+07:00 |
| Finalized | 2026-11-06T22:48:40+07:00 |
| Contributor | Codex |
| Related task | [WORK-2026-11-06-005](2026-11-06-005-five-year-corroboration.md) |
| Git state | main at 66e692d; prior uncommitted changes preserved |

## Objective

Finish remaining implementable work before graph construction: source/byline and
printed-affiliation reviews, conservative identity/work reconciliation, topic
staging, claim dispositions and an input-bound readiness freeze. No graph building,
materialization, imports or DB writes. Keep full-scope gaps and independent-review
requirements explicit rather than treating the frozen diagnostic tranche as a release.

## Changes and findings

- Added D026 and preserved the original five-year scope, quality thresholds, schema,
  all historical/frozen inputs and loaded graphs. New reviewed source ledger v3
  contains 19 input/PDF-bound records: five old + six parser/byline recoveries +
  eight printed affiliation mappings. Original statuses never changed.
- Corroboration v3: 55 source-eligible papers; 10 people, 11 authorships, 12 triples
  (nine author–paper pairs, nine organizations). Seven new public ORCID responses;
  zero new OpenAlex/PDF/model requests. Sixteen conflicting identifier mentions and
  absent public publication evidence remain withheld.
- Implemented `prepare-pregraph` with offline known-frame work/version guards,
  source/person/affiliation verification, organization staging, uncalibrated topic
  candidates, in-tranche citation candidates, claim dispositions and immutable
  content-addressed freeze receipts. It creates no graph artifact or DB writes.
- Current bundle v3: 55 accepted / 13 withheld source records; 318 known-frame work
  crosswalk records checked against known rosters/reserved IDs, no detected conflicts,
  no merges/global certification. Seventeen topic candidates on 16 papers remain
  unaccepted; 39 no-phrase abstentions. Zero in-tranche citation candidates.
- Original 345 queue rows: eight resolved / 337 withheld. All current 339 mixed-unit
  queue rows have withheld dispositions. Triage closure is not evidence completion.
- Two separate blank reviewer forms prepared: 68 development papers / 346 author
  positions each, with no predictions, acceptance flags, reviewer identities or
  invented judgments. These are development calibration forms, not held-out gold.
- Full request remains partial: 91 edition gaps, full enrichment/global canonical
  population, researcher/affiliation/topic coverage and independent quality not
  complete. `full_pregraph_ready=false`; graph construction remains unperformed.
- Status, roadmap, instructions, workflow and measured reports updated. Site source
  retains all 20 Plan sections and historical explorer payload. **Site v13 published**
  on the existing public URL; [receipt](../reference/sites-pregraph-publication-2026-11-06.json).

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run pytest` final v3 | 156 passed, exit 0 | ignored run `pytest-final-v3.log`; 11 new synthetic pregraph contract tests |
| `uv run research-network prepare-pregraph --help` | exit 0 | explicit config/output paths |
| Corroboration command with source/config/output v3 | exit 1 for unresolved claims; 68 outputs retained, no collection stop | `five-year-corroborated-v3/summary.json`; ignored `corroborate-v3.log` |
| `uv run research-network prepare-pregraph --config configs/five-year-pregraph-v3.yaml --output data/processed/five-year-pregraph-v3` | exit 1 correctly reports unmet full gates; outputs/freeze retained | `five-year-pregraph-v3/summary.json`, `freeze.json` |
| Same CLI with `SourceCache.get` raising on access | wrapper exit 0; expected CLI exit 1; identical replay | ignored `offline-replay-final.log` |
| Protected/raw evidence verification | 7,895 unchanged; 369 source objects verified; seven new ORCID descriptors, zero OpenAlex | ignored `verification.json` |
| Fresh read-only services check | GROBID alive, both Neo4j HTTP 200; 154/211 and 399/533 match task 005 counts; no writes | ignored `verification.json`; not a new pre/post claim |
| First system-Python ledger correction | `ModuleNotFoundError: scientific_network`; rerun under `uv run python` succeeded | v2 retained; v3 preserves literal printed names/markers |
| Pregraph v1/v2 iterations | preserved as historical outputs; v3 corrects specific missing-institution dispositions so they cannot borrow another accepted institution | regression `test_specific_missing_affiliation_cannot_borrow_another_institution` |
| Site build/static/HTTP checks | 20 Plan sections, two tabs, 266 unique IDs, zero embeds; unchanged payload; aggregate download/content passed | ignored `site-static-check.json`, `site-browser-limit.json` |
| Interactive browser QA | incomplete: navigation succeeded, next Playwright evaluation did not return; exec cell terminated | HTTP/static checks passed; JS/CSS/payload unchanged |
| Site push/package/publication | succeeded, v13; commit `554f47576c3c51bf3d142b9563ace99b6bc45209`; same public audience/URL | [receipt](../reference/sites-pregraph-publication-2026-11-06.json) |
| Hosted HTTP/static check | final result in hosted check/receipt; interactive browser QA remains incomplete | ignored `site-hosted-check.json` |
| `git diff --check` | exit 0 | whitespace check |

Current config: `configs/five-year-pregraph-v3.yaml`; method
`five-year-pregraph-readiness-v3`. All input/config/output hashes are in
`reports/five-year-pregraph-v3.metrics.json` and local `freeze.json`. Earlier
v1/v2 outputs/configs/ledgers remain historical and unchanged. Raw text/PDFs,
public ORCID bodies, support tables and reviewer forms remain ignored/local.

## Decisions

[D026](../decisions.md#d026--pregraph-evidence-closure-without-graph-construction-2026-11-06).
No graph schema, corpus boundary, release threshold or held-out assignment changes.

## Open issues and limitations

The user's full request is not finished: full source coverage, enrichment and
global canonical works are incomplete; topic quality and independent component
labels are unmeasured/not run. Missing/restricted source evidence and independent
review cannot be replaced by software checks, agent reviews or closing queue rows.
Blank development review forms cannot establish independent release accuracy.
Neither a graph nor an imported release is authorized by the freeze receipt.
No collection jobs remain running. Local preview is stopped at final teardown.
Project changes remain uncommitted; no project push requested or performed.

## Next step

Address the explicit failed gates in `reports/five-year-pregraph-v3.md`: verify
remaining accessible source routes, freeze a feasible larger prospective enrichment
and review design before scaling, reconcile canonical versions and obtain independent
labels. Keep all old/new tests untouched; do not build a release graph from this
failed full-readiness freeze.

## Corrections

None.
