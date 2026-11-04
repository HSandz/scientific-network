# Project specification

Current shared workspace: [AI Research Network — Plan & Report (2021–2025) (Sites)](https://ai-research-network-plan.hazy-tern-8113.chatgpt.site),
published 1 November 2026, read 2 November 2026, Site version 2 at inspection.
The [text snapshot](reference/sites-project-plan-2026-11-02.txt) preserves all 20
sections of that publication. It is a rendered-text capture; browser checklist
state and layout are not project results. The original snapshot stays unchanged;
the current expanded policy below supersedes its two-conference boundary. The
[revised Sites source snapshot](reference/sites-project-plan-2026-11-03.md) records
the full 20-section planning revision. Sites **version 3** was published on
3 November 2026; [the publication receipt](reference/sites-plan-publication-2026-11-03.json)
records its exact source commit/version and unchanged public audience. These
are historical snapshots; the current five-year Plan and evolving Report share
the same Site under D018/D019. See [the update workflow](sites-workflow.md).
The renamed two-tab Site was published as **version 4** on 4 November 2026;
[receipt](reference/sites-publication-2026-11-04.json),
[full Plan snapshot](reference/sites-project-plan-2026-11-04.md) and
[Report snapshot](reference/sites-progress-report-2026-11-04.md).
**Version 5** replaces the embedded explorer with native graph, chart, filter and
evidence components in the Report tab (D020); the complete Plan is unchanged.
[Current receipt](reference/sites-native-publication-2026-11-04.json),
[native Report snapshot](reference/sites-progress-report-2026-11-04-native.md).

## Course brief

Construct a meaningful social network using NLP. The original minimum is 2,000
nodes, 5,000 edges, ten distinct relationship types, and accuracy above 90%.
The brief permits narrowing an international topic to a smaller scope with at
least 1,000 nodes; this project retains the stronger original threshold.
Use a suitable graph DBMS, such as Neo4j. Submit a report of at least ten pages
covering task allocation, network rationale, collection/processing stack,
preprocessing, network statistics, achievements/limitations, and a real GitHub URL.
Wikipedia, news and academic-paper sources are permitted; Wikipedia is not the
chosen core corpus for this topic.

## Current planning baseline — five years, revised 4 November 2026

- Cover major AI and related flagship venues in **2021, 2022, 2023, 2024 and 2025**:
  **34 series / 170 venue–year candidates**, not a confirmed edition count (D018).
  See [scope policy](conference-scope.md), [temporal design](five-year-scope.md) and
  `configs/conference-scope-2021-2025.yaml`. Verify each edition independently;
  a no-2023-edition status does not exclude that series in other years.
- **Planning, documentation and Site updates only. No pipeline implementation or
  data collection under this revision.** D015 is historical 2023 authorization;
  current user instructions pause further execution. Preserve every config,
  manifest, split, graph, review ledger and report used by existing runs.
- One existing public Site has **Plan** and **Report** tabs (D019). The Plan shows
  the current target; the Report shows dated measured snapshots and limitations.
  Update/publish the Report after material project iterations using
  [the Site workflow](sites-workflow.md). It is not an automatic live database view.
- Five node types: Researcher, Organization, Paper, Topic, Venue. Store year and
  country as properties. Papers are deduplicated works, not PDF versions.
- Ten predicates as defined in [the schema](graph-schema.md). Separate R1–R4
  observed facts, R5 inferred topics, R6 curated taxonomy, and R7–R10 derivations.
- Paper-specific author–organization alignment, stable internal identities,
  resolvable evidence, reversible review decisions, and immutable raw inputs.
- Metadata-first acquisition, selective GROBID PDF parsing, organization linking,
  a versioned phrase baseline and supported multilabel topic classification.
- Neo4j Community with a compatible, pilot-verified GDS installation; documented
  NetworkX algorithms can provide checks/fallback. A small Streamlit demo suffices.
- Two people, eight weeks as a workload baseline. Actual course deadline and
  member availability remain to be entered in [the team record](team.md).

## Proposed release gates

| Gate | Required evidence |
| --- | --- |
| ≥2,000 resolved core researchers and ≥2,000 domain nodes | Deduplicated counts; unresolved/context/technical records excluded |
| ≥5,000 unique accepted factual edges | R1–R4 core-supported totals before projections |
| All ten predicates nonempty | Genuine semantic support and separate inventory |
| Global precision ≥95%, Wilson 95% lower bound >90% | 600-edge uniform frozen audit, two reviewers, adjudication |
| Per-type inspection | 100 edges/type or census; separate from the global estimator |
| No structural defects | Keys, endpoint types, provenance, orientation, no invalid self-loops |
| Coverage targets | 95% abstracts, 80% author–paper affiliation resolution, 80% topic paper coverage |
| NLP/component quality | Held-out precision, recall, F1, label support and error categories |
| Rebuild | Versioned inputs/configs, idempotent import, matching tables and graph counts |
| Delivery | Substantive ≥10-page report, real repository/release links, contributions and limitations |

Thresholds and configurations are proposals, not measured results. Structural
validation in this scaffold does not enforce the entire release protocol.

## Business questions and outputs

Use separate researcher collaboration, organization collaboration and directed
core citation projections to study bridges, collaboration communities, sector
mixing, topic portfolios and within-corpus influence. Do not run one heterogeneous
PageRank and describe its result as researcher influence.

Produce three evidence-backed findings and two investigation shortlists. Each
finding needs a statistic, denominator, at least two supporting papers and a
material limitation. Planned cases: an academia–industry partner map, a researcher
bridge profile and an organization topic comparison. Publication participation
does not establish current employment, nationality, contracts or commercial readiness.

## Scope and workload controls

Preserve the historical 100-paper NeurIPS/ICML pilot and 250-paper expanded
2023 diagnostics. All 5,046 legacy assignments and the expanded 925 test / 470
development / 13,514 pool allocation remain immutable. Before future enrichment,
reconcile cross-year/cross-venue versions, reserve old held-out versions and
prospectively budget venue–year diagnostics and independent annotation. Do not
apply old quotas to 170 candidates or multiply release targets by five. No new
samples are frozen in this task.

Five-year analysis must separate annual from cumulative graphs, recompute support
and thresholds within each analysis window, and disclose citation-age and
source-coverage differences. Count unique works/researchers once over the union;
annual counts can overlap and must not be summed as unique totals. The original
eight-week and 16 GB estimates do not size this scope. Re-estimate storage, runtime,
API allowance and reviewer hours before later implementation authorization.
Independent accuracy remains unmeasured. Prediction and years outside 2021–2025
remain optional. See [temporal scope and staging](five-year-scope.md).

## Lecturer confirmations to record in week one

Confirm acceptance of a heterogeneous academic network; the operational meaning
of “accuracy”; and whether topic hierarchy and derived predicates count toward
the ten types. If NLP F1 >90% is required, add it as a distinct acceptance gate.
These pending course decisions do not prevent scaffolding or source inspection.
