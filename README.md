# AI Research Network — AAAI and IJCAI, 2021–2025

This course project for **Social Media Network Analysis for Business** builds an
evidence-backed social network from AAAI and IJCAI main-track papers, 2021–2025.
The network connects researchers, papers, organizations, topics and venues. It is
used to analyze collaboration, citation and topic patterns for research-program
planning.

The release covers 13,617 papers from roster v10, matched to OpenAlex by DOI and
checked against title and author count. It is frozen as graph **v4
`release-d3c788c3114a`** (SHA-256
`6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`, bound by its
[content freeze](reports/release-v4/content-freeze-v4.json)). The submission
deadline was 11 November 2026. See [current status](docs/status.md) for what
remains open.

## Results

| Requirement or artifact | Frozen v4 evidence |
| --- | --- |
| Graph size | 47,875 nodes; 225,731 total edges; 32,189 resolved researchers |
| Course edge threshold | 110,026 unique factual R1–R4 edges; derived/topic/taxonomy edges counted separately |
| Relationship types | All 10 predicates are nonempty |
| OpenAlex coverage | 13,606/13,617 works matched (99.92%); 11 remain in review |
| Affiliation coverage | 48,259/65,469 matched author positions (73.71%); **fails the 80% target** |
| Topic coverage | 11,575/13,617 papers labeled (85.00%); coverage is not accuracy |
| Graph database | Isolated Neo4j Community 5.26; inventory, six integrity queries and idempotent replay pass |
| Network analysis | Five projections plus strict sensitivity, six figures/CSV tables, three source-backed findings, two shortlists |
| AI-assessed edge precision | **193/200 = 96.50%**, Wilson 95% **92.95%–98.29%**; AI-only numeric checks pass |
| Historical v3 edge audit | 176/200 = 88.00% (Wilson 82.77%–91.80%); gates failed; preserved |
| Topic agreement (historical, AI references) | Embedding micro F1 .4667, phrase baseline .2301; both miss the .95 precision target |

**All evaluation is AI-assessed.** Human validation was not performed, and
evaluator independence and verified course accuracy are not established. Wilson
intervals exclude evaluator mistakes, shared-model bias and dependence on
construction sources. The v4 correction (removing OpenAlex IDs with conflicting
ORCIDs) was motivated by the failed v3 audit, so the v4 sample is not an untouched
independent experiment. The [v4 evaluation package](reports/release-v4/README.md)
gives the full method, exposure, overlap and evidence-depth disclosures.

## Reports

- **Course report (English and Vietnamese, LaTeX):** [`report/latex/`](report/latex/README.md)
- Measured report source and figures: [`reports/final-report/report.md`](reports/final-report/report.md), [v4 figures](reports/final-report/figures-v4/captions.md)
- v4 evidence: [graph summary](reports/release-v4/graph-summary.json), [analysis](reports/release-v4/analysis.json), [findings](reports/release-v4/findings.md), [edge audit results](reports/release-v4/audit-results-agent-v2.json), [change manifest](reports/release-v4/change-manifest.json)
- Historical v3 package: [`reports/release-v3/`](reports/release-v3/README.md)
- Public Explorer: <https://scientific-network-explorer.pages.dev/>

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

A fresh clone does not include the graph file or the OpenAlex cache (both are
ignored). Restore them from the original sources and check the recorded hashes
using the [v4 restoration and reproduction guide](docs/reproduce-remediation-v4.md).
Reacquiring from the API is not a byte-identical substitute. The release database
is the isolated `neo4j-five-year` service on Bolt port 7689. The pilot and extended
databases are separate and preserved.

Analysis writes to a new path, because committed outputs are frozen:

```bash
uv run research-network analyze \
  --input data/processed/release-graph-v4/graph.json \
  --config configs/analysis-release-v1.yaml \
  --quality-config configs/quality-release-v1.yaml \
  --output reports/runs/manual-analysis.json
```

## Graph model

The graph has five labels: `Researcher`, `Paper`, `Organization`, `Topic` and
`Venue`. Its ten predicates are:

- Observed: `AUTHORED`, `AFFILIATED_WITH`, `PUBLISHED_IN`, `CITES`
- Inferred from text: `HAS_TOPIC`
- Curated taxonomy: `SUBTOPIC_OF`
- Derived from accepted core-paper evidence: `COAUTHORED_WITH`, `COLLABORATED_WITH`, `RESEARCHES_TOPIC`, `CONTRIBUTES_TO_TOPIC`

Read the [graph schema](docs/graph-schema.md) for evidence, identity and weight
rules. Researchers are never merged on similar names alone. Affiliation triples
stay paper-specific before aggregation, and ambiguous claims stay in the review
queue.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/scientific_network/` | Python package, one subpackage per pipeline stage; CLI `research-network` |
| `tests/` | Test suite (`uv run pytest`) |
| `configs/` | Versioned corpus, quality, analysis and evaluation configs; earlier versions kept for reproducibility |
| `queries/` | Neo4j constraints, inventory, integrity and analysis Cypher |
| `apps/research-explorer/` | Research Explorer frontend and API; `ops/azure/` holds its deployment |
| `reports/` | Measured results, receipts and figures, one folder per release |
| `report/latex/` | Course report sources |
| `docs/` | Requirements, design, workflows, decisions and the work log; start at [docs/README.md](docs/README.md) |

Raw downloads, graphs, models, credentials and database volumes are not tracked.
The repository is [github.com/HSandz/scientific-network](https://github.com/HSandz/scientific-network).
Its visibility and lecturer access are tracked in [status](docs/status.md).
