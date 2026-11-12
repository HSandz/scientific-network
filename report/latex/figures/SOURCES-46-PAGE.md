# Figure provenance and selection manifest

All measured report figures use frozen production v4, `release-d3c788c3114a`.
No graph, classifier, experiment, analysis result or evaluation judgment was
changed. The report builds from local figure files. PDF figures are vector
artifacts; matching 250 dpi PNGs support inspection and reuse. Long provenance
notes live in manuscript captions instead of embedded image footnotes.

## Reproduction

From the repository root, run:

```sh
.venv/bin/python report/latex/scripts/generate-figures.py
```

Requires the existing analysis environment (Matplotlib, NumPy, NetworkX).
The script checks literal SHA-256 pins for graph, analysis, summary and six source
CSVs before drawing. It reads inputs without writing to them and writes only
`report/latex/figures/`. Exact input hashes and bounded selections are recorded in
[`render-receipt.json`](render-receipt.json). Selection CSVs preserve stable
endpoint IDs, accepted edge IDs, distinct-paper support and fractional weights.
The ignored full graph is necessary only to regenerate network selections;
compiling the manuscript requires none of the ignored inputs.

Graph SHA-256: `6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`.
Analysis SHA-256: `580d1a6dbc21ef2ac17b820979830f3de157fc1b04d1c89f2580731f141701c9`.
Analysis methods and partition parameters remain those of the frozen release.

## Figure definitions

Each basename below supplies both `.pdf` and `.png`.

| Basename | Frozen input | Display and denominator |
| --- | --- | --- |
| `researcher-degree-ccdf` | `reports/final-report/figures-v4/researcher-degree-ccdf.csv` | Distinct coauthor-degree CCDF; denominator is all 32,189 resolved researchers, including isolates. The log x-axis displays positive degrees. |
| `component-sizes` | `reports/final-report/figures-v4/component-sizes.csv` | All 2,936 researcher components, ranked by size; isolates included, log y-axis. |
| `topic-trends` | `reports/final-report/figures-v4/topic-trends.csv` | Eight topics with greatest total fractional mass, in separate panels with shared axes. Each labeled paper divides mass one across its labels; annual denominator combines labeled AAAI and IJCAI papers. |
| `community-topic-profiles` | `reports/final-report/figures-v4/community-topic-profiles.csv` | First 12 communities in the stored size order; ten topics with greatest summed fractional mass in those stored profiles. Transposed heatmap with wrapped labels. Louvain seed 17, resolution 0.8. Each community stores only five topics: grey is unreported, not zero. Community IDs are local to this partition. |
| `sector-mixing` | `reports/final-report/figures-v4/sector-mixing.csv` | Symmetric sector matrix; cells count distinct organization-pair by core-paper supports. Unknown sectors remain explicit. The academia–academia cell is 10,956. |
| `top-cited-papers` | `reports/final-report/figures-v4/top-cited-papers.csv` | First ten stored in-degree leaders; complete wrapped titles and years. Counts are distinct in-corpus citing papers, without age normalization or external citations. |
| `coverage` | `reports/release-v4/graph-summary.json`, `coverage.topic_labeled_by_venue_year` | Labeled/all roster counts by venue and year; 11,575/13,617 overall. Inside each bar, the labeled count appears above the total. Labels indicate availability, not accuracy. |
| `organizations-network` | Accepted frozen v4 `COLLABORATED_WITH` edges | Replaces the dense 60-node map with twelve academia–industry pairs ranked by descending `support_count`, then stable source and target IDs. Eleven unique organizations. All topics combined; not the topic-specific 14-paper screen and not an induced network. `organizations-network-edges.csv` identifies every edge. |
| `researchers-network` | Accepted frozen v4 `COAUTHORED_WITH` edges | Focal researcher `researcher:openalex:A5017743551` (Bo An), plus twelve one-hop neighbors ranked by descending `support_count`, descending `fractional_weight`, then neighbor ID. All accepted edges induced on these 13 IDs: 24 edges. Spring layout seed 17, 400 iterations, paper-support weights. Gold focal node, teal neighbors; blue incident edges vary with support, grey neighbor edges use constant width. Node sizes distinguish focus only. Not the complete ego network. `researchers-network-edges.csv` identifies every edge. |
| `citations-network` | Accepted frozen v4 `CITES` edges | Focal paper `paper:aaai:2021:17325` (Informer). Select twelve of its 51 incoming neighbors by descending full-projection in-degree, then paper ID. Display only the twelve incoming edges to Informer, arrows from citing to cited; 13 papers. Not induced: other incoming edges and citations among the selected papers are omitted. Color redundantly indicates the printed citing year. `citations-network-edges.csv` identifies every edge. |

The three bounded views support inspection, not population inference. Their
selection rules favor repeated collaboration or cited neighbors and are not
random samples. Display names come directly from frozen node records; stable IDs,
not names, control selection. Provider identity and DOI-version uncertainties
remain those disclosed in the report.

## Diagrams and protected artwork

- `data-pipeline.tex`: report-local TikZ from the documented acquisition, resolver,
  classifier and graph materialization flow. Identity/affiliation and topic
  processing are parallel dependencies. The matching box explicitly points to
  the seven historical DOI exceptions; it does not retrospectively assert exact
  returned-DOI equality for every accepted v4 match.
- `system-architecture.tex`: report-local TikZ from the Python pipeline,
  `ops/azure/scripts/prepare-artifacts.py` and Explorer repositories. Graph JSON
  supplies Neo4j, SQLite evidence/affiliation records and offline analysis.
  Analysis does not construct the evidence ledger. Dashed flow supplies immutable
  analytics to FastAPI; graph/evidence reads also feed the read-only backend.
- `../assets/uet.png`: original user-supplied bitmap, unchanged. LaTeX preserves
  its aspect ratio; no redraw, recoloring or image preprocessing was performed.

The original 50-page compiled baseline and all rendered before/after contact
sheets are retained locally under ignored `../review/`. They are review evidence,
not build inputs or revised research artifacts.
