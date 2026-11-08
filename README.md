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

| Requirement or artifact | Current evidence |
| --- | --- |
| Graph size | 52,415 nodes; 275,438 total edges; 36,680 resolved researchers |
| Course edge threshold | 124,619 unique factual R1–R4 edges; derived/topic/taxonomy edges counted separately |
| Relationship types | All 10 predicates are nonempty |
| OpenAlex coverage | 13,606/13,617 works matched (99.92%); 11 remain in review |
| Topic coverage | 11,575/13,617 papers labeled (85.00%); this is coverage, not accuracy |
| Graph database | Neo4j Community 5.26 isolated service; v1/v2 inventory, integrity and idempotent replay passed |
| Network analysis | Five projections, six figures with tables, and three evidence-linked candidate findings |
| Independent quality | **Not measured.** Human edge reviews and topic labels have not been returned; the graph is not certified |
| Report | Sections 1–11 drafted with measured results; reviewer scores, real team details and final PDF remain pending |

Graph v2 is `release-5d830ffcbdf4`, SHA-256
`b79e456b22488ca8f753fb0884afd5c6a89afeeeaffec07d89ce83b2c5c141fb`. The
current graph and full source caches are local ignored artifacts; small reports,
figures, configurations and code are versioned. The graph meets the structural
size targets, but structural validation does not establish semantic accuracy.

The edge audit packet covers 200 globally sampled edges plus a separate sample of
10 per relation. The global sample has 50 edges reviewed by both reviewers. Topic
reviewer A and B each receive 30 of the 50 frozen papers, with 10 shared. Both
instruments are prepared for human review; neither is an evaluation result.

## Reproduce the local checks

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --group dev --extra analysis
uv run pytest
uv run research-network validate \
  --input data/processed/release-graph-v2/graph.json \
  --config configs/quality-release-v1.yaml \
  --require-size \
  --output reports/runs/manual-v2-validation.json
```

The graph file and OpenAlex cache are ignored and are not included in a fresh
clone. Their acquisition, build, import and analysis commands are recorded in the
[D040 release plan](docs/release-plan.md) and phase work logs. Do not rerun
acquisition without checking the configured API allowance and local cache first.
The release database is the isolated `neo4j-five-year` service on Bolt port 7689;
the pilot and extended databases are separate and preserved.

To reproduce named-projection analysis with local release inputs, choose a new
output path because the committed workspace output is frozen:

```bash
uv run research-network analyze \
  --input data/processed/release-graph-v2/graph.json \
  --config configs/analysis-release-v1.yaml \
  --quality-config configs/quality-release-v1.yaml \
  --output reports/runs/manual-analysis.json
```

## Review and report artifacts

- [Release findings](reports/release-v1/findings.md)
- [Analysis metrics](reports/release-v1/analysis.json)
- [Graph v2 summary](reports/release-v1/graph-v2-summary.json)
- [Frozen graph and review hashes](reports/release-v1/freeze.json)
- [Topic-review assignment manifest](reports/release-v1/audit/topic-review-allocation.json)
- [Edge review sheet](reports/release-v1/audit/edge-review-sheet.html)
- Topic review packets: [reviewer A](reports/release-v1/audit/topic-label-sheet-reviewer-A.html), [reviewer B](reports/release-v1/audit/topic-label-sheet-reviewer-B.html)
- [Draft academic report](reports/final-report/report.md)
- [Evaluation protocol](docs/evaluation.md)

Reviewer CSV exports should preserve the paper/edge IDs, use the assigned A/B
reviewer label, and follow the packet instructions. For an empty topic set, leave
the label fields blank and note that no taxonomy leaf applies. Return completed
edge and topic exports for scoring. The topic master sheet and frozen test
membership must not be edited.

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

This local branch has not been pushed or tagged. Do not treat the remote README,
release or Site as updated until the project owner publishes the final version.
