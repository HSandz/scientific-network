# Explorer descriptive extension v1

This is a separate, exploratory descriptive artifact over the unchanged corrected
release-v4 graph. It neither modifies the release nor evaluates accuracy. No model,
external API, tuning, random sampling or stochastic computation is involved.

Reproduce to an **unused** path (the command refuses files and symlinks):

```bash
uv run python -m scientific_network.analysis.explorer_derived \
  --graph data/processed/release-graph-v4/graph.json \
  --config configs/explorer-analysis-release-v1.yaml \
  --output reports/runs/WORK-2026-11-10-011/reproduced-derived.json
cmp reports/explorer-analysis-release-v1/derived.json \
  reports/runs/WORK-2026-11-10-011/reproduced-derived.json
```

`derived.json` records graph, config and method-source SHA-256 values, complete
configuration, selection rules and definitions. Seed is null: all ordering uses
explicit stable-ID tie-breaks. Output SHA-256:
`bb0da2d2d2f9b23cec053ceb3cc31514a614b7a85b7672d38791e409d93eb37d`.
Graph SHA-256:
`6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`.

## Definitions and measured outputs

Citation in-degree counts accepted CITES with both endpoints core papers in the
configured years. All papers, including uncited papers, belong to their venue/year
cohort. Percentile is the empirical fraction with in-degree less than or equal to
the focal paper, including ties. This is not global impact, exposure normalization,
prediction or independent validation. The ten cohorts cover all 13,617 core papers;
10,140 have zero **incoming** in-corpus citations. This differs from citation
isolates (no incoming **or outgoing** edges).

| Venue/year | All papers | Zero incoming citations |
| --- | ---: | ---: |
| AAAI 2021 | 1654 | 716 |
| AAAI 2022 | 1319 | 662 |
| AAAI 2023 | 1578 | 988 |
| AAAI 2024 | 2331 | 2057 |
| AAAI 2025 | 3028 | 2894 |
| IJCAI 2021 | 586 | 274 |
| IJCAI 2022 | 678 | 347 |
| IJCAI 2023 | 639 | 480 |
| IJCAI 2024 | 790 | 724 |
| IJCAI 2025 | 1014 | 998 |

Organization persistence uses distinct accepted R8 evidence support-paper IDs,
intersected with core papers. Top 25 pairs are ordered by full-period paper count,
then edge ID. Counts by year include zero years. Inferred topic counts overlap for
multilabel papers. Missing affiliations and labels are unknown; co-publication
neither proves a continuous partnership nor funding, contracts or employment.

The first pair, Chinese Academy of Sciences–University of Chinese Academy of
Sciences, has 303 distinct supporting papers: 49/52/43/58/101 in 2021–2025,
respectively. These are observed co-publication years, not partnership duration.

Researcher components use accepted R7 edges and include isolates. The largest 25
are selected by size then stable ID; representative = highest coauthor degree,
then stable ID. A representative's bounded Ego is an illustration, not complete
component membership. Membership hashes identify components within this graph;
they do not stabilize Louvain community IDs across graph versions.

The API verifies the extension's graph hash against the frozen analysis input.
Azure preparation embeds it in a **new immutable runtime artifact directory**;
old runtime artifacts honestly show unavailable extension/strict summaries.
See [implementation receipt](../research-explorer-implementation-2026-11-10.md).
