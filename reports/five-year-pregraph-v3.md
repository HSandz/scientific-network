# Pregraph readiness — 6 November 2026

**Full pregraph readiness: not achieved. No graph was built or imported.**
The frozen development tranche is technically prepared; the full five-year
project still requires source coverage, broader enrichment/work reconciliation,
quality calibration and independent labels. Closing a queue as withheld does not
resolve its underlying evidence gap or make the full project ready.

D026 / WORK-2026-11-06-006. `five-year-pregraph-readiness-v3`;
`configs/five-year-pregraph-v3.yaml`. The prior v1/v2 preparation outputs are
historical diagnostics, not the current freeze. This report concerns 68 new
frozen development papers, separate from the historical 250-paper 2023 tranche.

| Measure | Measured result |
| --- | ---: |
| Frozen development papers / author positions | 68 / 346 |
| Input/PDF-bound source reviews | 19 |
| Source-accepted / withheld papers | 55 / 13 |
| Corroborated unique people / authorship supports | 10 / 11 |
| Reviewed author–paper–organization triples | 12 |
| Affiliated author–paper pairs / organizations | 9 / 9 |
| Abstracts on source-accepted papers | 54 / 55 |
| Known-frame work crosswalk records | 318 |
| Known-frame quarantined records | 0 |
| Topic candidates / papers with candidates | 17 / 16 |
| Accepted topic labels / accepted citations | 0 / 0 |
| Current mixed-unit queue rows, withheld | 339 |
| Original 345 queue rows: resolved / withheld | 8 / 337 |
| New public ORCID responses / new OpenAlex requests | 7 / 0 |
| Graph construction / imports / held-out acquisition | 0 / 0 / 0 |

The 318 work rows combine already exposed historical/new diagnostics and are
checked against the known official roster and reserved membership using exact
DOI/provider/source identifiers and transitive version guards. Equal titles
can quarantine potential versions; they never merge works. Zero known-frame
conflicts is not proof of exhaustive canonical work resolution or an all-corpus
work count. Historical support tables are not automatically accepted into the
new tranche, and these staging counts must not be added to old graph totals.

The source ledger now has 19 records: the previous five plus six parser/byline
recoveries and eight printed affiliation reviews. The recoveries remove institution
names from bylines, restore truncated/missing headers and fix a split diacritic.
Thirteen genuine title/byline disagreements remain withheld. All original metadata
and GROBID statuses are preserved; no OCR/parser-success counts were rewritten.

Twelve affiliation triples need both a corroborated person/publication and an
exact institution within that author's metadata, supported by printed markers.
Two additional laboratories printed for an already affiliated author remain
withheld: another accepted institution cannot validate those laboratories.
Missing affiliations, conflicting stable crosswalks and absent public works are
not repaired by a name-only merge or a current-profile affiliation.

Topic outputs are uncalibrated literal phrase candidates. Their spans are tied
to official title/abstract evidence. Thirteen papers are withheld before topic
assignment, 39 abstain without supported phrases, and 16 have candidates. No
candidate becomes an accepted graph relationship. No in-tranche citation target
was found; no context/external paper was acquired to manufacture citation support.

## Actual prerequisite gates

| Gate | Status | Evidence or remaining dependency |
| --- | --- | --- |
| Frozen input integrity | passed | Inputs/reserved IDs pinned and rechecked |
| Diagnostic source triage | passed | All 68 have accepted/withheld dispositions |
| All planned editions resolved | failed | 79 eligible; 51 unresolved / 40 unavailable |
| Full enrichment and work resolution | failed | Bounded diagnostics only; full collection not done |
| Researcher release target | failed | 10 in new tranche; target 2,000; historical counts separate |
| Affiliation coverage | failed | 9/346 selected author–paper pairs (2.60%); target 80% |
| Abstract coverage in accepted source tranche | passed | 54/55 (98.18%); all selected: 67/68 (98.53%) |
| Accepted topic paper coverage | failed | 0/55; target 80%; candidates do not count |
| Topic calibration/taxonomy approval | unmeasured | Draft taxonomy; independent labels unavailable |
| Independent component quality | not run | Requires independent reviewer annotations |
| Global canonical work resolution | failed | Alternate-title/inaccessible-source versions unresolved |

The graph-dependent factual-edge/predicate and final 600-edge audit gates are not
run before graph construction. No structural test establishes accuracy above 90%.
Scope and thresholds remain unchanged; this freeze does not authorize graph building.

## Frozen artifacts and review handoff

Local ignored bundle: `data/processed/five-year-pregraph-v3/`. Contains paper
and edition dispositions, work and organization crosswalks, accepted authorship
and affiliation support, topic/citation candidates, prior/current queue dispositions,
and `freeze.json`. The freeze pins every output plus summary/input/config hashes.
The public [aggregate JSON](five-year-pregraph-v3.metrics.json) contains no PDFs,
full abstracts, raw ORCID records or annotation text.

Two separate **blank development review packets** are prepared under
`data/annotations/five-year-development-review-v1/`: 68 paper and 346 author-position
forms per reviewer. Predictions and acceptance flags are hidden; reviewer IDs,
judgments and notes are blank. The tracked manifest records their hashes.
These are exposed development papers for calibration, not held-out gold labels,
an independent release audit or completed reviewer work. Keep each original
reviewer form and adjudication separate. Old/new reserved test IDs remain untouched.

## Verification

- `uv run pytest`: **156 passed**, exit 0; 11 new synthetic pregraph contract tests.
- `prepare-pregraph` run/replay: exit **1**, correctly reporting unmet gates;
  outputs retained and identical. Additional source-disabled replay passes.
- **7,895 protected artifacts** unchanged; **369 source objects** verified,
  including negative public ORCID responses. Seven new ORCID responses, zero
  OpenAlex requests. No full-corpus/PDF/model collection.
- Fresh end-of-task read-only checks: GROBID alive; both Neo4j HTTP 200 with
  **154/211** and **399/533**, matching task 005. No DB writes in this task.
- User request to finish all prerequisites remains **partial**, because the full
  source/enrichment/canonical population and independent labels are not complete.

Next work must address the failed gates: verify remaining official source routes
without bypassing access restrictions, freeze a feasible prospective larger
collection/review design before scaling, reconcile canonical versions, and obtain
independent labels for calibration/evaluation. A diagnostic graph could be a
separate limited deliverable later; this task does not construct it or relabel it
as the planned five-year release.
