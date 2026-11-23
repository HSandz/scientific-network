# Project documentation

Start with [status](status.md). It records the current state, what is still open
and the next step. Results and evidence live under [`reports/`](../reports/),
mainly [release v4](../reports/release-v4/README.md) and the
[final report](../reports/final-report/report.md).

## Requirements and plan

- [Project specification](project-plan.md): course brief, business questions and evaluation caveats
- [Release plan (D040)](release-plan.md): scope, evidence rules and requirement-to-evidence table for the 11 November release
- [Correction amendment, 9 November](correction-amendment-2026-11-09.md): authorizes the v4 identity correction and its single edge audit
- [Decision register](decisions.md), with an index of current and historical decisions
- [Roadmap](roadmap.md): implemented capabilities
- [Team and contributions](team.md)

## Design and data

- [Graph schema and derivation](graph-schema.md): five labels, ten predicates, evidence and weight rules
- [Data dictionary and storage](data-dictionary.md)
- [Sources, collection and redistribution](source-policy.md)
- [Network analysis](analysis.md): named projections and metrics
- [Quality evaluation](evaluation.md): what is measured and how results may be stated

## Reproduce, evaluate and deliver

- [Restore and reproduce frozen v4](reproduce-remediation-v4.md) (cited by the submitted report)
- [Agent audit workflow](agent-audit-workflow.md) and [historical v3 scoring/rendering](reproduce-agent-evaluation.md)
- [Post-audit findings on the v3 graph](post-audit-findings.md)
- [Local submission and delivery checklist](local-submission-checklist.md)
- [Shared Plan & Report Site workflow](sites-workflow.md), [current Site report source](../reports/site-report.md) and [publication records](reference/README.md)

## Working on the project

- [Work log](work-log/README.md): one entry per session, from the [template](templates/work-log.md)
- [Fresh-session release prompt](prompts/agent-release-completion.md)
- [Review and annotation CSV templates](templates/)

## Historical, kept in place

These describe superseded work. They stay at their original paths because frozen
receipts, the release plan or `AGENTS.md` refer to them by path. The historical
measured reports are listed here too.

- [Optional human reviewer handoff, 9 November](reviewer-handoff.md): superseded by agent-led evaluation
- [Complete pregraph prerequisite plan](pregraph-completion-plan.md) (D028) and [five-year source-route triage](five-year-source-triage.md)
- [Five-year collection workflow](five-year-collection.md) and [edition readiness table](five-year-edition-readiness.csv)
- [2023 expanded collection workflow](extended-workflow.md) and [NeurIPS/ICML pilot workflow](pilot-workflow.md)
- Measured historical reports: [pilot](../reports/pilot-v1.md), [expanded 2023](../reports/extended-v1.md),
  [five-year collection](../reports/five-year-collection-v2.md), [latest source recovery](../reports/five-year-source-recovery-v10.md),
  [pregraph readiness](../reports/five-year-pregraph-v3.md)

Everything else that was superseded is in the [archive](archive/README.md).
