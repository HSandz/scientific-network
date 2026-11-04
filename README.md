# International AI Research Network

Course project for **Social Media Network Analysis for Business**. Construct an
evidence-backed network of researchers, organizations, papers, topics, and venues
across **major AI and related flagship conferences in 2021–2025**.
The [five-year plan](docs/five-year-scope.md) covers 34 series and 170 venue–year
candidates requiring edition verification; this is not 170 confirmed editions.
NeurIPS and ICML were course examples; their existing data is a historical pilot.

The plan and evolving report share the [AI Research Network — Plan & Report (2021–2025) Site](https://ai-research-network-plan.hazy-tern-8113.chatgpt.site).
The scope, acceptance criteria, and source snapshots are recorded in
[the local plan](docs/project-plan.md). The existing Site is published as version 5
with **Plan** and **Report** tabs, including native graph, charts, filters and
evidence inspection; [publication/update workflow](docs/sites-workflow.md).

**Status: five-year planning/Site revision only; pipeline implementation and
collection paused (D018).** `configs/conference-scope-2021-2025.yaml` is the new
planning registry. Historical `configs/conference-scope.yaml` and executable
`configs/corpus-extended-v2.yaml` remain unchanged for 2023 reproducibility.
No five-year executable config, split or collection has been created. Read the [expanded workflow](docs/extended-workflow.md),
[measured status](docs/status.md) and edition ledger for actual coverage;
not every planned venue is accessible.

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
`analyze` and `evaluate` remain placeholders and return exit code 2 with their next
implementation step. `audit-precision` is a separate Wilson-interval utility,
not an independent audit or an accuracy result.

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

The full entity/evidence explorer remains planned. The GitHub remote, release tag,
final report PDF, measured quality summary, member names/IDs, and code license
must be supplied before submission. No remote is configured by this scaffold.
