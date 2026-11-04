# Final report outline

Status: outline only; no final ten-page report exists. The [historical pilot](../pilot-v1.md)
has measured two-venue diagnostics; [expanded 2023 results](../extended-v1.md) and
[the reviewed candidate](../evidence-review-v1.md) are partial diagnostics.
The [current scope](../../docs/five-year-scope.md) covers **2021–2025**, 34 series
and 170 venue–year candidates requiring edition verification, not 170 confirmed
editions. Five-year collection has not started. Explain edition/no-edition states,
cross-year versions, temporal coverage and stratified evaluation. Keep all
2023 results separate from future five-year findings. The evolving
[Site Report tab](https://ai-research-network-plan.hazy-tern-8113.chatgpt.site/#report)
is a progress publication and does not replace the required final ≥10-page report.
Course minimum: **10 pages**; target **16–18 substantive pages**, excluding cover
and optional appendices. Replace every placeholder with measured, versioned evidence.

| Section | Pages (guide) | Content |
| --- | --- | --- |
| Problem and business motivation | 1 | Scope, research questions, decisions supported and boundary |
| Team allocation | 0.5 | Names/IDs, responsibilities, cross-review and contribution evidence |
| Sources and collection | 1.5 | Proceedings selection, technology stack, manifest/access/counts/provenance |
| Preprocessing and entity resolution | 2 | Cleanup, version matching, people/organizations, aligned affiliations |
| NLP methods | 2 | GROBID, topic definitions/baseline/model, splits and annotation |
| Graph design and construction | 2 | Five node meanings, ten predicates, DBMS, support and weights |
| EDA and network statistics | 1.5 | Annual/cumulative counts, missingness by venue–year, components, degree and coverage |
| Social network and business analysis | 2.5 | Annual/cumulative projections, temporal collaboration/topic comparisons, citation-age controls and three supported cases |
| Quality and robustness | 2 | Exact audit counts/intervals, recall/F1, coverage, errors and sensitivity |
| Conclusion and limitations | 1 | Achieved/unmet targets, bias, boundary, unresolved data and limitations |
| References and reproducibility | 1 | Primary docs, exact versions, actual GitHub URL and release tag |

## Planned figure/table set

Collection/quality overview; degree/components; collaboration communities with
topics; organization sector/topic comparison; core citation map. Save figure data
and state projection, filter, counting convention, graph version and denominator
in every caption. Sparse graphs and selection effects must remain visible.

## Submission checklist

- [ ] At least ten substantive pages and all required course sections.
- [ ] Measured graph size, all ten types, factual/derived totals and source evidence.
- [ ] Independent global/per-type audits plus component recall/F1 and coverage.
- [ ] Real member contributions, real GitHub URL and exact release tag.
- [ ] Acquisition/rebuild instructions, source manifest, schema and data dictionary.
- [ ] Permitted entity/edge exports and evidence ledger; Neo4j export or load path.
- [ ] Three source-supported business cases, robustness and material limitations.
- [ ] Both teammates reproduce the graph and principal outputs.
- [ ] Credentials/restricted full texts excluded; source rights/code license stated.

Final report PDF: **TBD**. Repository URL/release: **TBD**. Optional demo video: **TBD**.
