# Bilingual figure provenance and selection

Every measured figure uses frozen production v4, `release-d3c788c3114a`.
No graph, classifier, analysis result or evaluation judgment was changed.
Each basename below has a vector PDF and a 250 dpi PNG in both `en/` and `vi/`.
Eight plots plus two shared TikZ diagrams produce ten numbered figures per PDF.
The original manifest remains in [SOURCES-46-PAGE.md](SOURCES-46-PAGE.md).

## Reproduction and pins

From the repository root:

```sh
.venv/bin/python report/latex/scripts/prepare-data.py
.venv/bin/python report/latex/scripts/generate-figures.py --language en
.venv/bin/python report/latex/scripts/generate-figures.py --language vi
```

Generation requires the existing analysis environment (Matplotlib, NumPy,
NetworkX) and exact local frozen inputs. It writes only report assets, reads the
stored measurements, and never reruns graph construction or topic classification.
Ordinary PDF compilation requires only the included local figure PDFs.

| Frozen input | SHA-256 |
| --- | --- |
| `data/processed/release-graph-v4/graph.json` | `6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90` |
| `reports/release-v4/analysis.json` | `580d1a6dbc21ef2ac17b820979830f3de157fc1b04d1c89f2580731f141701c9` |
| `reports/release-v4/graph-summary.json` | `c6c6e78195500bfaf68cf1f758215824ea239056eefa9ae442edfb0a378b8408` |
| `data/interim/release-v1/works.jsonl` (example source verification) | `2b7f3bc15ad46398e9f55ece060536050215238355e9580d2689f00005f55047` |

The works path is verified against the local protected-hash record; it is not a
plot-generation dependency. All six CSV pins and rendering-library versions are
recorded in [en/render-receipt.json](en/render-receipt.json) and
[vi/render-receipt.json](vi/render-receipt.json). The script checks those pins
before drawing. Receipts have identical data-series hashes and node/edge
selections across languages. Official titles, names and stable IDs remain in
their original form; axes, sectors, topics and explanatory labels are localized.

## Active plots

CSV paths below are relative to `reports/final-report/figures-v4/`.

| Basename | Input | Counting and display rules |
| --- | --- | --- |
| `publications` | Summary `coverage.topic_labeled_by_venue_year` | The `eligible` series, not the labeled series: all 13,617 official main-track papers by year and venue. Includes all 11 unmatched papers. Stacked counts share a zero baseline. |
| `topic-trends` | `topic-trends.csv` | Eight topics with greatest total fractional mass across both venues. A labeled paper divides mass one across its accepted labels. Annual denominator is labeled papers from both venues; all panels share one vertical scale. |
| `researcher-structure` | `researcher-degree-ccdf.csv`, `component-sizes.csv` | Combined degree CCDF and component rank plot. CCDF denominator: all 32,189 accepted researchers, including isolates; positive degrees displayed on log axes. Component plot includes all 2,936 components, including singletons; log y-axis. No fitted power-law claim. |
| `sector-mixing` | `sector-mixing.csv` | Symmetric matrix of distinct organization-pair by core-paper supports. Mirrored cross-sector cells repeat the same support and must not be added twice. Unknown sector remains visible. Academia–academia: 10,956; academia–industry: 3,533. |
| `organizations-network` | Accepted v4 `COLLABORATED_WITH` edges | Twelve academia–industry pairs by descending distinct-paper `support_count`, then stable source/target IDs. Eleven unique organizations; repeated names are intentional. A horizontal pair ranking, not an induced graph or the 14-paper topic-specific screen. All topics combined. |
| `community-topic-profiles` | `community-topic-profiles.csv` | First 12 communities in stored size order; ten topics with greatest summed fractional mass in those stored profiles. Louvain seed 17, resolution 0.8. Each community stores only its five leading topics: grey is unreported, not zero. Community IDs belong to this partition. |
| `researchers-network` | Accepted v4 `COAUTHORED_WITH` edges | Bo An (`researcher:openalex:A5017743551`) plus twelve one-hop neighbors by descending support, descending fractional weight, then stable neighbor ID. All accepted induced edges among those 13 IDs: 24 edges. Spring seed 17, 400 iterations, support weights. Focal node gold, others teal; focal edge widths reflect support, grey neighbor edges constant. Node size distinguishes focus only. |
| `top-cited-papers` | `top-cited-papers.csv` | First ten stored in-degree leaders, with complete wrapped official titles and years. Counts are distinct in-corpus citing papers; external citations and publication-age normalization are absent. |

[en/organizations-network-edges.csv](en/organizations-network-edges.csv) and
[en/researchers-network-edges.csv](en/researchers-network-edges.csv), with identical
Vietnamese counterparts, record accepted edge IDs, endpoints, paper support and
fractional weights. The two bounded views favor repeated collaboration and are
not random samples. Stable IDs control selection, not display names.

## Shared diagrams and example evidence

- [bilingual-pipeline.tex](bilingual-pipeline.tex): official collection → matching
  → parallel researcher/affiliation and NLP branches → graph materialization →
  validation/storage. Describes the actual acquisition/resolver/classifier flow;
  its caption retains the seven historical DOI exceptions. Full diagram labels
  are supplied separately in English and Vietnamese.
- [bilingual-example.tex](bilingual-example.tex): actual frozen v4 nodes/edges for
  ECG ODE-GAN, `paper:aaai:2021:16086`, DOI `10.1609/aaai.v35i1.16086`, OpenAlex
  `W3176135934`. Official entry:
  <https://ojs.aaai.org/index.php/AAAI/article/view/16086>.
  Accepted authors are Tomer Golany (`A5022512211`) and Kira Radinsky
  (`A5029708595`); both have paper-specific Technion (`I174306211`) observations.
  Daniel Freedman is an official byline author but has no accepted authorship.
  The assigned topic is `topic:generative-modeling`. Solid arrows denote observed
  edges, dashed topic arrow denotes inference, and dashed undirected line denotes
  the derived coauthor pair. Short relationship codes and a full predicate legend
  prevent labels overlapping entity names.
- [../data/construction-example.json](../data/construction-example.json) preserves
  exact accepted nodes, edges and the two affiliation observations, compared for
  object equality against frozen v4 by the report verifier. This is measured
  evidence, not a synthetic illustration. One shared institution creates no
  organization collaboration; one paper cannot create a topic-profile edge.
- [../assets/uet.png](../assets/uet.png): original protected artwork, byte-identical
  to `4b265c8`. Included at its original aspect ratio without recoloring or crop.

## Selection changes from the original report

Retained and localized topic trends, community profiles, sector mixing, the
organization-pair ranking, citation ranking and bounded researcher neighborhood.
Combined two researcher-structure plots. Added the publication chart and real
construction example. Retained/relabelled the corrected pipeline. Removed the
separate coverage chart (now one compact table), bounded citation-neighborhood
plot (ranking and concrete Informer example suffice), and system-architecture
TikZ diagram (implementation detail). Original files and provenance remain.

Final page renders, six contact sheets, high-resolution details and typography
proof are local in `../review/redesign/`. Their inspection is recorded in
[../REVIEW-BILINGUAL.md](../REVIEW-BILINGUAL.md).
