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
| Graph database | Neo4j Community 5.26 isolated service; corrected graph inventory, integrity and idempotent replay passed |
| Network analysis | Five projections, six figures with tables, and three evidence-linked candidate findings |
| Quality evaluation | **Not measured.** Agent-led source review is authorized; evaluator support and real judgments/scoring are next. Human validation is not performed |
| Report | Sections 1–11 drafted with measured results; reviewer scores, real team details and final PDF remain pending |

Graph v3 is `release-9d4a6fb20f63`, SHA-256
`c23ef82c97fcb539b4b1c279e8ff42378bdb102e80fe851acf1a42e816a727b8`.
It corrects taxonomy metadata/provenance without rerunning the frozen classifier.
The old graph, freeze, packets and reports remain preserved; the replacement
package is [reports/release-v2/freeze-v3.json](reports/release-v2/freeze-v3.json). The
current graph and full source caches are local ignored artifacts; small reports,
figures, configurations and code are versioned. The graph meets the structural
size targets, but structural validation does not establish semantic accuracy.

The user selected **agent-led evaluation** on 9 November. Human annotations are
optional and do not block execution. Follow [the agent workflow](docs/agent-audit-workflow.md)
and [fresh-session execution prompt](docs/prompts/agent-release-completion.md).
The [protocol config](configs/evaluation-agent-release-v1.yaml) declares the method;
agent provenance/scoring support still needs implementation before actual review.
Report AI-assessed precision and topic agreement with AI-assigned labels, with
evaluator/source limitations; do not present these as human validation or verified
course accuracy. Frozen graph, classifier, samples and historical packets stay intact.

## Reproduce the local checks

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --group dev --extra analysis
uv run pytest
uv run research-network validate \
  --input data/processed/release-graph-v3/graph.json \
  --config configs/quality-release-v1.yaml \
  --require-size \
  --output reports/runs/manual-v3-validation.json
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
  --input data/processed/release-graph-v3/graph.json \
  --config configs/analysis-release-v1.yaml \
  --quality-config configs/quality-release-v1.yaml \
  --output reports/runs/manual-analysis.json
```

## Review and report artifacts

- [Release findings](reports/release-v2/findings.md)
- [Fresh analysis metrics](reports/release-v2/analysis.json)
- [Graph correction summary and preservation checks](reports/release-v2/graph-summary.json)
- [Replacement freeze and review hashes](reports/release-v2/freeze-v3.json)
- [Topic-review assignment manifest](reports/release-v1/audit/topic-review-allocation.json)
- Preserved human edge packets: [reviewer A](reports/release-v2/audit/edge-review-sheet-v2-reviewer-A.html#reviewer=A), [reviewer B](reports/release-v2/audit/edge-review-sheet-v2-reviewer-B.html#reviewer=B)
- Topic review packets: [reviewer A](reports/release-v1/audit/topic-label-sheet-reviewer-A.html), [reviewer B](reports/release-v1/audit/topic-label-sheet-reviewer-B.html)
- [Draft academic report](reports/final-report/report.md)
- [Active agent audit and scoring workflow](docs/agent-audit-workflow.md)
- [Fresh-session execution prompt](docs/prompts/agent-release-completion.md)
- [Preserved optional human handoff](docs/reviewer-handoff.md)
- [Technical verification and remaining human inputs](reports/release-v2/technical-verification.json)
- [Evaluation protocol](docs/evaluation.md)

New agent review exports and evidence ledgers go to the separately versioned paths
in the active workflow. Do not fill or rebind old human edge forms. Topic packets
may be reused by exact-byte reference for blind input; completed outputs stay
separate. Distinguish a considered empty topic set from an unreviewable paper.
The topic master, allocation and frozen test membership must not be edited.

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

WORK-037 recorded an earlier 9 November remote check at `951b9c5`, with no tags.
Remote state was not refreshed for this protocol amendment; verify it before
authorized delivery. This amendment performs no push, tag, Site publication or
submission.
