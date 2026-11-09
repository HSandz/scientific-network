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
| AI-assessed edge precision | **176/200 = 88.00%**, Wilson 95% **82.77%–91.80%**; course point/project precision gates **FAIL**; zero missing reviews |
| Topic agreement with AI references | Embedding micro F1 **.4667**, phrase **.2301**; test coverage 90%/26%; neither reaches .95 micro precision |
| Report | Measured report complete; local PDF/package checks recorded in current status; real team/course facts pending |

Graph v3 is `release-9d4a6fb20f63`, SHA-256
`c23ef82c97fcb539b4b1c279e8ff42378bdb102e80fe851acf1a42e816a727b8`.
It corrects taxonomy metadata/provenance without rerunning the frozen classifier.
The old graph, freeze, packets and reports remain preserved; the replacement
package is [reports/release-v2/freeze-v3.json](reports/release-v2/freeze-v3.json). The
current graph and full source caches are local ignored artifacts; small reports,
figures, configurations and code are versioned. The graph meets the structural
size targets, but structural validation does not establish semantic accuracy.

Source-backed agent evaluation is complete under the
[agent workflow](docs/agent-audit-workflow.md) and
[protocol](configs/evaluation-agent-release-v1.yaml). A/B used separate fresh
contexts and froze blind topic judgments before edge exposure. All 350 edge
assignments and 60 topic assignments are complete; 11 actual edge disagreements
were source-adjudicated with original votes retained. Edge overlap agreement is
39/50 (78%; kappa .1852); topic overlap exact agreement is 10/10. These results
are **AI-assessed**, with human validation not performed, evaluator independence
and verified course accuracy not established. Precise runtime model/provider IDs
are unknown; Wilson intervals do not cover evaluator error or shared-source bias.

The audit found a resolver omission: conflicting `author.observed_orcids` arrays
are retained in raw/full source records but ignored by singular-ORCID conflict
handling. See [post-audit findings](docs/post-audit-findings.md). The frozen graph,
classifier, samples and historical receipts remain unchanged. Any correction
requires a separately versioned graph and new audit; failed gates are preserved.

## Reproduce the local checks

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --group dev --extra analysis --extra report
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

## Evaluation, report and local delivery

- [AI edge results and failed gates](reports/release-v3/audit-results-agent.json)
- [Both frozen topic classifiers and per-label metrics](reports/release-v3/topic-eval-agent.json)
- [Evaluation package and completion receipts](reports/release-v3/README.md)
- [Evaluation limitations and source reuse](reports/release-v3/evaluation-limitations.md)
- [Academic report](reports/final-report/report.md)
- [Exact scoring, rendering and packaging commands](docs/reproduce-agent-evaluation.md)
- [Local submission and separately authorized delivery checklist](docs/local-submission-checklist.md)
- [Frozen analysis](reports/release-v2/analysis.json) and [candidate findings](reports/release-v2/findings.md)
- [Graph correction summary](reports/release-v2/graph-summary.json) and [content freeze](reports/release-v2/freeze-v3.json)

The new source ledgers/exports preserve actual judgments and evidence locators;
old blank human packets and frozen test membership/allocation are unchanged.
Global and per-type audit samples are reported separately. Topic scoring gives
each paper weight one and distinguishes considered empty sets from unreviewable
references; none of the real topic assignments is unreviewable.

The local PDF/ZIP remain ignored; their checked paths/hashes and source checkpoint
are recorded in the final work entry/package receipt linked from
[current status](docs/status.md). The package contains permitted source files,
small reports/figures and the rendered report. It excludes raw/full graph data,
models, credentials and database volumes. Rescoring requires restoring original
permitted inputs, then checking their freeze hashes; it cannot run from the ZIP
alone. Real names, student IDs, actual contributions, lecturer access and course
AI-use rules remain pending. No human annotation wait is required.

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
unpushed; the GitHub HTTP check returned 504, so public lecturer access remains
not verified. The project Site still reflects an earlier publication and is not
live-synchronized with these local results. No push, release tag, Site publication,
invitation or submission was performed. Those actions require separate explicit
authorization after the local package is reviewed.
