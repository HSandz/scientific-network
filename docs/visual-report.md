# Visual report

The shared [Plan & Report Site](https://ai-research-network-plan.hazy-tern-8113.chatgpt.site)
contains the current five-year plan and a dated evolving report, with native
graph controls, charts, conference coverage and evidence inspection in its Report
tab. No iframe or separate embedded document is used (D020). The standalone
HTML below remains an immutable **2023 snapshot**; the Site identifies it separately
from the 402/538 local candidate. See [publication/update workflow](sites-workflow.md).
Five-year pipeline work and collection are paused under D018.

Open [the standalone HTML report](../reports/extended-v1.html) directly in a browser.
It embeds the graph, charts, source references, scripts and licensed fonts; no
server, internet connection, API key or Neo4j connection is required. Opening an
external source link requires internet access.

The report visualizes the existing expanded diagnostic snapshot: **399 nodes,
533 relationships, 245 papers and 17 covered conference editions**. Roster size,
diagnostic sample size and accepted graph size have separate denominators. This
is an output explorer, not the course's final ten-page written report or an
independent semantic evaluation.

## Explore the output

- Switch between the full network, factual R1–R4, researcher coauthorship and
  organization collaboration. Typed isolates stay visible in social projections.
- Filter by conference or search by entity name/ID. Search includes matches and
  their immediate neighbors within the selected projection/conference.
- Select a node with the mouse or Enter/Space; select a relationship in its
  inspector to see source links, locators, hashes, method versions and support.
  The expandable entity list provides a keyboard alternative to the graph.
- Drag nodes to rearrange them or drag the background to pan. Use zoom, Fit or
  Reset. Positions are a deterministic display layout, not measured centrality,
  similarity, community membership or edge strength.
- Browse all 34 conference series and distinguish unavailable rosters from measured
  zeros. Export the currently filtered conference table as CSV, or download all
  embedded report data as JSON.
- Use **Print / PDF** to print the current graph view with all 34 conference rows.
  The table filter is restored afterward. Reset the graph first to print all nodes.

Conference filtering follows accepted paper support, including exact
researcher–paper–organization observations and the supporting papers of derived
edges. A citation appears only when both papers belong to that conference. Topic
hierarchies retain only supported topics and their ancestors. Stored social
support counts/fractional weights describe the full snapshot; filtering does not
recalculate them.

The HTML explicitly separates observed, inferred-topic, curated-taxonomy and
derived relationships. Only the **369 factual R1–R4 edges** count toward the
5,000-edge requirement. Eight predicates are nonempty; independent accuracy is
**not measured** and release gates remain unmet.

## Generate a new report offline

```bash
uv sync --locked --group dev
uv run research-network report \
  --input data/processed/extended-graph-v1.json \
  --metrics reports/extended-v1.metrics.json \
  --config configs/quality.yaml \
  --scope-config configs/corpus-extended-v2.yaml \
  --output reports/extended-v1-review.html
```

Choose a new output filename. Existing files, symlinks and input aliases are
refused. The generator checks graph structure with derived-support validation,
reconciles graph counts/version, and verifies graph/quality/scope hashes against
recorded metrics. It does not query Neo4j, validate source-cache bytes, rerun
collection or perform the independent audit. Recorded task 006 checks are labeled
as historical.

The `report` command expects the expanded diagnostic metrics format, not an
arbitrary Neo4j export. Its inputs are ignored local data artifacts and the small
recorded metrics/config files; a fresh clone needs the matching graph restored or
reproduced. The HTML itself is self-contained and includes public metadata, short
topic phrases and provenance, with full abstracts omitted. Node properties use an
explicit allowlist; no `.env` file is read by the generator.

Implementation: `src/scientific_network/reporting/`; NumPy is an explicit core
dependency for NetworkX's seeded force layout. Report method:
`standalone-html-report-v1`. See [D016](decisions.md#d016--standalone-read-only-visual-report-2026-11-03)
and [WORK-2026-11-03-007](work-log/2026-11-03-007-html-report.md) for checks and limits.
