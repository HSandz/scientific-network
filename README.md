# AI Research Network — AAAI and IJCAI, 2021–2025

This course project builds an evidence-backed social network from AAAI and IJCAI
main-track papers from 2021 through 2025. The network connects researchers,
papers, organizations, topics and venues, then analyzes collaboration, citation
and topic patterns for research-program planning.

**Submission deadline:** 11 November 2026.
**Release scope:** 13,617 papers from roster v10, matched to OpenAlex by DOI and
checked against title and author count. See the [D040 release plan](docs/release-plan.md)
and [current status](docs/status.md).

## Current measured state

| Requirement or artifact | Corrected v4 evidence |
| --- | --- |
| Graph size | 47,875 nodes; 225,731 total edges; 32,189 resolved researchers |
| Course edge threshold | 110,026 unique factual R1–R4 edges; derived/topic/taxonomy edges counted separately |
| Relationship types | All 10 predicates are nonempty |
| OpenAlex coverage | 13,606/13,617 works matched (99.92%); 11 remain in review |
| Affiliation coverage | 48,259/65,469 matched author positions (73.71%); 48,259/65,507 official positions (73.67%); **FAIL 80% target** |
| Topic coverage | 11,575/13,617 papers labeled (85.00%); coverage is not accuracy |
| Graph database | Isolated Neo4j Community 5.26; v4 inventory, all six integrity queries and idempotent replay pass |
| Network analysis | Five freshly recomputed projections plus strict sensitivity, six figures/CSV tables, three source-backed findings and two shortlists |
| V4 AI-assessed edge precision | **193/200 = 96.50%**, Wilson 95% **92.95%–98.29%**; frozen AI point/Wilson numeric checks **PASS**; verified course accuracy not established |
| Historical v3 AI edge audit | **176/200 = 88.00%**, Wilson 95% **82.77%–91.80%**; course point/project precision gates **FAIL** |
| Historical topic agreement with AI references | Unchanged embedding micro F1 **.4667**, phrase **.2301**; test coverage 90%/26%; exposed references, no new untouched holdout |
| Report/package | V4 measured report; build from its committed source using the reproduction command; measured delivery artifacts belong to the new package receipt |

Current graph **v4 `release-d3c788c3114a`**, SHA-256
`6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`,
is bound by [its content freeze](reports/release-v4/content-freeze-v4.json).
[The dated amendment](docs/correction-amendment-2026-11-09.md) authorizes a
separate correction of the observed-ORCID omission and one prospective edge
audit, while preserving the old graph, failed audit, classifier and package.

The correction unions normalized checksum-valid singular and observed-array
ORCIDs across **all matched works**, finding **4,492 conflicting OpenAlex IDs**
and **zero malformed IDs**. Missing/null ORCID remains allowed; malformed
nonempty identity evidence would be withheld globally. It removes **4,491
researchers, 49 unsupported organizations and 8,722 accepted authorships**;
one source conflict was already absent from the graph. All core papers,
publication/citation claims, official byline denominators, taxonomy and frozen
topic predictions/scores/excerpts/evidence remain. Only a missing unresolved
reason is added to newly authorless papers; all other paper properties remain.
R7–R10, affected support/weights and every analysis projection were recomputed.
See the [summary](reports/release-v4/graph-summary.json),
[change manifest](reports/release-v4/change-manifest.json) and
[analysis comparison](reports/release-v4/analysis-comparison.json).

Institution support is 48,259/50,437 accepted authorships (95.68%), but this
conditional diagnostic excludes withheld positions and does not rescue the
failed coverage target. The largest researcher component now contains
20,776/32,189 (64.5%), versus 73.6% historically. The top bridge candidate is
Bo An; the corrected strict-filter betweenness top-20 overlap is 0/20, so ranks
are leads for inspection. Citation and paper-topic projections remain exactly
unchanged; organization portfolios change with the surviving affiliations.

All evaluation is **AI-assessed**: human validation was not performed, evaluator
independence and verified course accuracy are not established. Exact runtime
model/provider IDs are unknown; Wilson intervals exclude evaluator mistakes,
shared-model bias and construction-source dependence. The old audit found the
identity omission and motivated this correction, so prior sample/source exposure
must be disclosed. New edge contexts do not own the historical topic labels.
No threshold tuning or repeated correction/sample cycle is authorized to obtain
a passing score. [Historical results](reports/release-v3/README.md) remain intact.

The new edge-only audit ran once: **350/350 assignments**, 300 unique edges,
200 uniform global edges and ten-per-type supplements, with 50 overlap edges.
Global outcomes are **193 correct, one incorrect, six unverifiable, zero
missing**; unverifiable counts as incorrect. Overlap agreement is **49/50 (98%),
kappa .6599**. Supplements are 9/10 for CONTRIBUTES_TO_TOPIC, 8/10 for
RESEARCHES_TOPIC and 10/10 otherwise, reported separately from global precision.
The new result passes the frozen **AI-assessed numeric checks only**; human
validation and verified course accuracy remain unestablished.

The [exposure receipt](reports/release-v4/sample-exposure-v2.json) records seven
repeated semantic edges among 300, zero new-global overlap with any old sample,
24/516 supporting papers in the previous explicit packet frame, and **177/237
raw OpenAlex batch-response hashes** overlapping prior packets/ledgers. Those
177 response objects are not a repeated-paper count. Correction was motivated
by the old audit; the new draw is not an untouched independent experiment.
Main evidence across 350 assignments is 215 primary-source/135 secondary-only,
all reusing construction sources. For two R10 aggregates B inspected **10/35
CAS** and **17/107 USTC** supports against the frozen minimum-three-paper
predicate; full `support_count` correctness is not exhaustively certified.

A [full-source consistency check](reports/release-v4/source-population-verification-v2.json)
verifies retained authorship/reference objects for all **13,606 matched works**,
**65,469 positions** and **341 raw response hashes**. This is source-byte equality,
not independent identity accuracy. The
[historical-topic reuse receipt](reports/release-v4/historical-topic-reuse-v2.json)
proves frozen prediction/evidence/taxonomy equality and records zero new topic
judgments. The failed .95 topic-precision and 80% affiliation-coverage targets
remain visible regardless of the new edge score.

## Reproduce the local checks

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --group dev --extra analysis --extra report
uv run pytest
uv run research-network validate \
  --input data/processed/release-graph-v4/graph.json \
  --config configs/quality-release-v1.yaml \
  --require-size \
  --output reports/runs/manual-v4-validation.json
```

The graph file and OpenAlex cache are ignored and are not included in a fresh
clone. Their acquisition, build, import and analysis commands are recorded in the
[D040 release plan](docs/release-plan.md) and phase work logs. Do not rerun
acquisition without checking the configured API allowance and local cache first.
See [the v4 correction/reproduction instructions](docs/reproduce-remediation-v4.md)
for frozen source restoration, correction and current analysis commands.
The release database is the isolated `neo4j-five-year` service on Bolt port 7689;
the pilot and extended databases are separate and preserved.

To reproduce named-projection analysis with local release inputs, choose a new
output path because the committed workspace output is frozen:

```bash
uv run research-network analyze \
  --input data/processed/release-graph-v4/graph.json \
  --config configs/analysis-release-v1.yaml \
  --quality-config configs/quality-release-v1.yaml \
  --output reports/runs/manual-analysis.json
```

## Evaluation, report and local delivery

- [Corrected graph summary](reports/release-v4/graph-summary.json) and [content freeze](reports/release-v4/content-freeze-v4.json)
- [Fresh analysis](reports/release-v4/analysis.json), [comparison](reports/release-v4/analysis-comparison.json) and [source-backed findings](reports/release-v4/findings.md)
- [Corrected figures and CSV source tables](reports/final-report/figures-v4/captions.md)
- [V4 evaluation package, exact reproduction and limitations](reports/release-v4/README.md)
- [V4 AI edge results and numeric checks](reports/release-v4/audit-results-agent-v2.json)
- [Prospective edge sample and assignment summary](reports/release-v4/audit/sample-summary.json)
- [V4 completion/source bindings](reports/release-v4/completion-receipt-v2.json) and [original votes/ledgers](reports/release-v4/completed/)
- [Historical AI edge results and failed gates](reports/release-v3/audit-results-agent.json)
- [Historical frozen-topic AI metrics](reports/release-v3/topic-eval-agent.json)
- [Historical completed evaluation package](reports/release-v3/README.md)
- [V4 academic report draft](reports/final-report/report.md)
- [V4 reproduction and restoration instructions](docs/reproduce-remediation-v4.md)
- [Historical scoring/rendering instructions](docs/reproduce-agent-evaluation.md)
- [Local submission and separately authorized delivery checklist](docs/local-submission-checklist.md)

Global audit samples and per-type supplements stay separate. Topic scoring gives
each paper weight one and distinguishes considered empty sets from unreviewable
references; none of the historical real topic assignments is unreviewable.
Those historical references and scores remain frozen; this correction performs
no new topic evaluation. The new edge-only scorer binds its own actual runs,
source ledgers, CSV assignments and completion/adjudication records.

The old PDF/HTML/ZIP and their checked hashes remain historical and unchanged.
Build the v4 package from the committed measured-report sources with the renderer
command in [the report](reports/final-report/report.md) and reproduction guide.
`reports/release-v4/local-package-receipt-v2.json` records actual output paths,
source commit, page count, member hashes/CRC and visual checks after that source
build; it is intentionally outside its own source snapshot. No measured page
count or package QA is preclaimed here. Submission artifacts exclude raw/full
graph data, models, credentials and database volumes. A fresh clone or ZIP cannot rescore without restoring
original permitted ignored inputs and verifying their freeze hashes; current API
reacquisition is not byte-identical restoration. Real names, student IDs, actual
human contributions, lecturer access and course AI-use rules remain pending.
Human annotation is optional; no routine scoring task is reserved for the user.

## Graph model

The graph has five labels: `Researcher`, `Paper`, `Organization`, `Topic` and
`Venue`. Its ten predicates are:

- Observed: `AUTHORED`, `AFFILIATED_WITH`, `PUBLISHED_IN`, `CITES`
- Inferred from text: `HAS_TOPIC`
- Curated taxonomy: `SUBTOPIC_OF`
- Derived from accepted core-paper evidence: `COAUTHORED_WITH`, `COLLABORATED_WITH`, `RESEARCHES_TOPIC`, `CONTRIBUTES_TO_TOPIC`

Read the [graph schema](docs/graph-schema.md) for evidence, identity and weight
rules. Researchers are never merged from similar names alone. Affiliation triples
remain paper-specific before aggregation, and ambiguous claims stay in the review
queue.

## Project records

- [Project specification and business questions](docs/project-plan.md)
- [Release plan (D040)](docs/release-plan.md)
- [Current handoff and phase checklist](docs/status.md)
- [Work-log index](docs/work-log/README.md)
- [Team and contribution record](docs/team.md)
- [Data and redistribution policy](docs/source-policy.md)

Historical 2023 pilot and multi-venue source-recovery artifacts are retained for
reproducibility. They are not the current release graph or evidence of current
release quality. The public project Site is **AI Research Network — Plan & Report
(2021–2025)**; it is updated once after final results, not kept synchronized with
this local workspace. The repository URL is
[github.com/HSandz/scientific-network](https://github.com/HSandz/scientific-network).

A read-only 9 November remote check returned main
`05ac5d83922c54bd006034e5c7296de00e811f72` and no tags. Local commits remain
unpushed; the new bounded GitHub HEAD check returned **HTTP 404**, so public
lecturer access remains **not verified**. Eight supporting DOI links returned
HTTP 200 in [the same check](reports/release-v4/report-external-link-checks-v4.json);
these statuses do not establish permanent availability or scientific correctness. The project Site still reflects an earlier publication and is not
live-synchronized with these local results. No push, release tag, Site publication,
invitation or submission was performed. Those actions require separate explicit
authorization after the local package is reviewed.
