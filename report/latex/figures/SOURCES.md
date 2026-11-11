# Figure source manifest

All PNG files in this directory are local copies; the report does not depend on
ignored run directories or on the source images outside this LaTeX project.

| Local file | Source artifact | Graph version | Definition |
| --- | --- | --- | --- |
| `researcher-degree-ccdf.png` | `reports/final-report/figures-v4/researcher-degree-ccdf.png` | `release-d3c788c3114a` | Researcher coauthorship degree CCDF; all resolved researchers including isolates |
| `component-sizes.png` | `reports/final-report/figures-v4/component-sizes.png` | `release-d3c788c3114a` | Connected components in the researcher projection; isolates included |
| `community-topic-profiles.png` | `reports/final-report/figures-v4/community-topic-profiles.png` | `release-d3c788c3114a` | Louvain seed 17, resolution 0.8; fractional inferred-topic profiles |
| `sector-mixing.png` | `reports/final-report/figures-v4/sector-mixing.png` | `release-d3c788c3114a` | Distinct organization-pair by core-paper support; symmetric sector matrix |
| `topic-trends.png` | `reports/final-report/figures-v4/topic-trends.png` | `release-d3c788c3114a` | Inferred topic share among labeled papers, fractional allocation |
| `top-cited-papers.png` | `reports/final-report/figures-v4/top-cited-papers.png` | `release-d3c788c3114a` | Within-corpus directed citation in-degree |
| `coverage.png` | `reports/final-quality-sprint/figures/coverage.png` | `release-d3c788c3114a` | Labeled and unlabeled paper share by venue-year |
| `researchers-network.png` | `reports/final-report/network-views-v4-v1/researchers-network.png` | `release-d3c788c3114a` | Deterministic bounded selection: 100 researchers, 90 induced edges |
| `organizations-network.png` | `reports/final-report/network-views-v4-v1/organizations-network.png` | `release-d3c788c3114a` | Deterministic bounded selection: 60 organizations, 1,119 induced edges |
| `citations-network.png` | `reports/final-report/network-views-v4-v1/citations-network.png` | `release-d3c788c3114a` | Deterministic bounded selection: 80 papers, 22 induced edges |

The two TikZ source figures (`data-pipeline.tex` and
`system-architecture.tex`) are drawn in this LaTeX project from the documented
implementation and schema; they introduce no measured values.
