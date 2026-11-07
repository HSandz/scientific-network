# International AI Research Network

> **Current direction (D040, 8 Nov 2026):** the submission graph covers AAAI and
> IJCAI 2021–2025 (13,617 papers from roster v10), built from DOI-matched OpenAlex
> evidence. Follow the [release plan](docs/release-plan.md) and the
> [current status](docs/status.md). The status notes below describe earlier
> iterations; they will be rewritten once release results exist.

Course project for **Social Media Network Analysis for Business**. Construct an
evidence-backed network of researchers, organizations, papers, topics, and venues
across **major AI and related flagship conferences in 2021–2025**.
The [five-year plan](docs/five-year-scope.md) covers 34 series and 170 venue–year
candidates requiring edition verification; this is not 170 confirmed editions.
**Submission deadline: 11 November 2026.** The [execution readiness plan](docs/five-year-execution-plan.md)
sets dated tasks, acceptance checks, resource assumptions and freeze cutoffs.
The [170-row planning ledger](docs/five-year-edition-readiness.csv) is unverified.

NeurIPS and ICML were course examples; their existing data is a historical pilot.

The plan and evolving report share the [AI Research Network — Plan & Report (2021–2025) Site](https://ai-research-network-plan.hazy-tern-8113.chatgpt.site).
The scope, acceptance criteria, and source snapshots are recorded in
[the local plan](docs/project-plan.md). The existing Site is published as version 18
with **Plan** and **Report** tabs, including native graph, charts, filters and
evidence inspection; [publication/update workflow](docs/sites-workflow.md).

**Status: official source recovery v10 and frozen development diagnostics (D038 / WORK-021).**
The current roster has **98 eligible editions / 91,355 included records** across
94,857 observations; 22 roster/adapter editions and 40 publisher-access candidates
remain incomplete, with 10 verified no-edition findings. MICCAI 2024 is reconciled
at 856 accepted research records; MICCAI 2022, AAMAS 2023 and all five ICLR years
remain unresolved. No new split, enrichment or graph was produced. See [v10 source results](reports/five-year-source-recovery-v10.md)
and [current handoff](docs/status.md). The P02 no-go for broader enrichment remains.
WORK-010 reviewed official route leads for the 15 unresolved ICDM/ICRA/IROS
venue-years. WORK-020 then captured hash-bound ICDM 2025 accepted-list, CFP,
BlueSky and program pages. The accepted list has 175 entries, but a short-paper
classification conflict, incomplete program/proceedings reconciliation and
unclear metadata reuse terms keep ICDM 2025 unresolved; all 15 ICDM/ICRA/IROS
years remain unresolved. The existing public Site remains at v18: after local DNS
recovered, its supported source helper still failed before checkout, so no Site
source audit, build or publication occurred.
WORK-021 used the connected browser to recapture the official ACM Multimedia
2024 accepted-ID file (1,149 unique IDs; matching the prior body hash) and review
the regular-paper and BNI calls. The regular call clarifies length-neutral review;
the BNI call places accepted papers in main proceedings. The 1,150 acceptance
statistic remains unreconciled, the program view is incomplete, and metadata
reuse terms are unknown, so the edition remains unavailable in v10. P02 remains
no-go with one reviewer of unknown hours and no second independent reviewer
confirmed. The local Report refresh is not live: the supported Sites helper
failed before checkout, leaving the public Site at v18. See [D038 and the
current handoff](docs/status.md).
WORK-011 found official accepted-list and program route leads for selected ACM and
SIAM venue-years, but local DNS and publisher 403s prevented source captures or
proceedings reconciliation. All 40 publisher-access dispositions remain unchanged;
all 42 current v10 output hashes verify.
WORK-012 found a more specific CIKM 2025 accepted-list/proceedings route, but no
hash-bound local capture or complete reconciliation. WORK-013 measured available
workspace resources; P02 remains no-go because the full work frame, isolated
database storage and provider costs are still unmeasured. The user reports one
reviewer with unknown hours; a second independent reviewer remains unconfirmed.
WORK-014 added standalone hash-bound edge-audit sample/scoring utilities. WORK-015
implemented named projection metrics for `analyze`; its CLI smoke used only the
synthetic fixture. WORK-016 implemented the separate component `evaluate`
contracts for frame-bound double review, adjudication, component metrics and core
coverage. Its synthetic packet tests are protocol-only; the real quality config is
not frozen and no complete independent labels are available. The latest full suite
passed 218 tests with one parameterized pending-stage test skipped. P01/P02 and
source-backed analysis remain incomplete; see [the latest handoff](docs/status.md).

`configs/conference-scope-2021-2025.yaml` is the
planning registry. Historical `configs/conference-scope.yaml` and executable
`configs/corpus-extended-v2.yaml` remain unchanged for 2023 reproducibility.
Current roster config: `configs/corpus-five-year-v10.yaml`; v1–v9 remain historical.
The [five-year workflow](docs/five-year-collection.md) adds frozen diagnostics and
bounded metadata acquisition. The preserved v2 diagnostic frame had **79 eligible editions, 75,655 included records;
67/68 diagnostic papers acquired; 170 new test groups preserved.** No five-year
graph or independent semantic score yet. See [measured revision 2](reports/five-year-collection-v2.md)
and [current handoff](docs/status.md). Its frozen sample still uses v2; do not
silently substitute the newer roster or redraw held-out IDs.

**Existing implementation: staged multi-venue pipeline.** Official roster discovery, frozen splits, pilot
metadata/PDF acquisition, GROBID headers, conservative identity/affiliation resolution,
phrase-baseline topics and transactional Neo4j loading are implemented. Independent
semantic accuracy, the complete release graph and final analysis remain pending.
The offline test example is explicitly synthetic. See the [pilot workflow](docs/pilot-workflow.md)
for stage commands and the limitations of this first implementation.

Read [current status and next steps](docs/status.md) for the latest handoff and
the [work log](docs/work-log/README.md) for completed tasks, checks and open issues.

Open the [interactive HTML report](reports/extended-v1.html) to explore the current
399-node / 533-edge diagnostic snapshot, conference coverage and source evidence.
It works offline; see [report usage and regeneration](docs/visual-report.md).

The subsequent [evidence review](reports/evidence-review-v1.md) recovered all
250 diagnostic metadata records and produced a separate 402-node / 538-edge
candidate. Two PDF byline conflicts remain withheld. The HTML and loaded databases
retain the earlier snapshot; see [review commands](docs/evidence-review.md).

## Quick start

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). The offline checks require
neither Docker nor API credentials.

```bash
uv sync --locked --group dev
uv run research-network schema
uv run research-network validate \
  --input tests/fixtures/synthetic_graph.json \
  --output reports/runs/synthetic-validation.json
uv run pytest
```

For a virtualenv/pip alternative, see [setup](docs/setup.md). `uv.lock` fixes package
versions. The source adapters, model revisions, and thresholds must be validated
and frozen during the pilot.

Optional local services:

```bash
cp .env.example .env
# Set a local Neo4j password in .env before starting services.
docker compose up -d neo4j
docker compose --profile nlp up -d grobid
```

Neo4j pilot Browser: <http://localhost:7474>. The expanded service is at
<http://localhost:7475> (`docker compose --profile extended up -d neo4j-extended`). GROBID: <http://localhost:8070>.
Services bind to localhost and keep data in Docker volumes. Run
`queries/00_constraints.cypher` in Neo4j Browser to initialize constraints.
GDS is deliberately not auto-installed; its version must be checked against the
pinned Neo4j image during the pilot. See [setup](docs/setup.md).

## Requirements and proposed release gates

| Requirement | Project decision | Current evidence |
| --- | --- | --- |
| At least 2,000 nodes | Additionally require 2,000 resolved core researchers | Pilot collected; release target pending |
| At least 5,000 edges | 5,000 unique accepted factual R1–R4 edges | Pilot only; release target pending |
| Ten relationship types | All ten predicates must have genuine support | Implemented; eight nonempty in [expanded report](reports/extended-v1.md) |
| Accuracy above 90% | Propose edge precision ≥95%, with 95% Wilson lower bound >90% | Not measured; lecturer confirmation pending |
| Suitable graph DBMS | Neo4j Community, with version-checked GDS or documented NetworkX fallback | Live import/replay verified; GDS pending |
| NLP construction | GROBID headers, affiliation linking, supported multilabel topics | Pilot implemented; phrase baseline uncalibrated |
| Report of at least 10 pages | Target 16–18 substantive pages | [Report outline](reports/final-report/outline.md) |

The [evaluation protocol](docs/evaluation.md) separates independent semantic
auditing from software tests, precision from recall, and requirements from results.

The new [PDF/header diagnostic report](reports/five-year-headers-v1.md) records
68 PDFs / 66 parsed headers and 255 unaccepted affiliation candidates. Two parser
failures and source/byline issues remain in review; no five-year graph is loaded.

## Graph model

| Predicate | Endpoints | Evidence class |
| --- | --- | --- |
| `AUTHORED` | Researcher → Paper | Observed |
| `AFFILIATED_WITH` | Researcher → Organization | Observed, paper-specific |
| `PUBLISHED_IN` | Paper → Venue | Observed |
| `CITES` | Paper → Paper | Observed |
| `HAS_TOPIC` | Paper → Topic | Inferred topic |
| `SUBTOPIC_OF` | Topic → Topic | Curated taxonomy |
| `COAUTHORED_WITH` | Researcher ↔ Researcher | Derived |
| `COLLABORATED_WITH` | Organization ↔ Organization | Derived |
| `RESEARCHES_TOPIC` | Researcher → Topic | Derived, ≥2 distinct core papers |
| `CONTRIBUTES_TO_TOPIC` | Organization → Topic | Derived, ≥3 distinct core papers |

See [schema and derivation rules](docs/graph-schema.md) and
[data contracts](docs/data-dictionary.md). Symmetric pairs are stored once.
An affiliation describes a publication-time observation, not current employment.

## Repository map

```text
configs/                     corpus, quality, topic taxonomy, analysis settings
src/scientific_network/
  collect/                   official proceedings, enrichment, retrieval
  preprocess/                text, TEI, mentions
  resolve/                   canonical identities, affiliations, review history
  nlp/                       topic baseline, classifier, abstention
  graph/                     schema, structural validation, derivation helpers
  analysis/                  named projections and business findings
  evaluation/                independent audit and held-out evaluation
app/                         optional Streamlit artifact preview
queries/                     Neo4j constraints, integrity and analysis queries
data/{manifests,raw,interim,processed,annotations}/
reports/                     measured outputs, figures, final report outline
docs/                        plan, contracts, annotation, sources, roadmap, team
tests/fixtures/              small invented evidence and graph examples
```

The stage runner exposes `discover`, `split`, `acquire`, `extract`, `resolve`,
`classify`, `validate`, `build`, `analyze`, and `evaluate`. Run `--help` on any stage.
`analyze` reports five named graph projections and descriptive metrics. Synthetic
inputs are protocol-only; non-synthetic graphs require configured size gates, a
matching post-build receipt, and a frozen analysis/evidence-filter config. It does
not produce business findings or certify release quality; see [analysis workflow](docs/analysis.md).
`evaluate` scores frame-bound component labels and coverage; synthetic inputs are
protocol-only, while real scoring requires a reserved test frame, frozen quality
config and complete eligible-core coverage denominator. It cannot verify held-out
membership, reviewer identity or independence, or certify a release. The final
edge audit is a separate post-build workflow: `freeze-audit-sample` prepares a new
hash-bound reviewer form for a synthetic fixture or a post-build-ready graph, and
`score-edge-audit` checks two-review packets. `audit-precision` is a separate
Wilson-interval utility, not an independent audit or an accuracy result.

Start with the [expanded-scope roadmap](docs/roadmap.md). Both teammates' roles,
review responsibilities, and contribution placeholders are in
[the team record](docs/team.md).

## Data, demo, and submission

Official proceedings define the corpus. OpenAlex, public OpenReview records, ROR,
and selectively parsed PDFs provide claim-specific enrichment. Wikipedia is an
optional enrichment source; the assignment also permits academic papers.
See [source and redistribution policy](docs/source-policy.md).

An optional synthetic/local artifact preview is available after
`uv sync --locked --extra app --group dev`:

```bash
uv run streamlit run app/main.py
```

The full entity/evidence explorer remains planned. The release tag,
final report PDF, measured quality summary, member names/IDs, and code license
must be supplied before submission. Configured origin: [HSandz/scientific-network](https://github.com/HSandz/scientific-network); remote access/reproduction must still be checked before submission.

The [development corroboration report](reports/five-year-corroboration-v1.md)
records D025: five reviewed source overlays, 10 corroborated researchers,
11 authorship supports and one affiliation triple. These are staging tables,
not an imported five-year graph or independently measured accuracy.

The [pregraph readiness report](reports/five-year-pregraph-v3.md) records the current
freeze: 55 source-accepted diagnostics, 12 affiliation triples and explicit failed
full-population gates. `prepare-pregraph` constructs no graph and returns 1 while
those prerequisites remain unmet. Scope, independent quality and release targets
remain incomplete; see the current handoff before proceeding.
