# Independent-source verification preparation

Task2C listed **48 bounded public URLs**, retrieved **45** immutable responses and
recorded **3** failures. Source URLs, UTC retrieval timestamps, SHA-256, cache paths,
licensing uncertainty and source roles are in `source-provenance*.json` and
[evidence/source-records.jsonl](evidence/source-records.jsonl). Full responses/PDFs
stay ignored. Every retrieved object was hash-verified during packet generation.
No OpenAlex reacquisition, ORCID alias recycling, paid service or access-control
bypass occurred. The two 403 hosts were stopped; a 404 was recorded, not worked
around with invented content. Search results supplied leads; reported observations
below come from cached retrieved sources, not search snippets.

## Coverage of investigation

This is targeted evidence preparation, not a representative semantic evaluation.
Some sources index several positions. The ledger includes 60 unique target positions:

| Candidate mechanism | Targeted positions | With retrieved source | Independent adjudicated person references |
| --- | ---: | ---: | ---: |
| Exact-DOI alternate work | 18 | 18 | 0 |
| Declared alias | 17 | 5 | 0 |
| Formatting | 9 | 9 | 0 |
| Remaining name variants | 8 | 8 | 0 |
| Unchanged provider/raw position | 8 | 6 | 0 |

The plan specifically includes an official paper for every one of the 18 alternate
recoveries, one representative paper for each of the five alias provider IDs,
eight formatting provider IDs, six unresolved providers plus two selected by
withheld-position impact, and six unchanged cases from the existing assignment
sample. Additional owner-page position associations explain the larger counts and
unretrieved targets. Those associations are search leads, not identity confirmations.
The 60 diagnostic targets do not change frozen sample membership or its probabilities.

## Useful verified source observations; identities remain unadjudicated

- **Daniel Kroening / DeepSynth**, DOI `10.1609/aaai.v35i9.16935`: the retrieved
  maintained bibliography contains the exact title, author list and an outgoing
  link to that exact DOI. The publisher PDF was separately retrieved; its first
  page provides paper-specific byline/email context. This is a substantially better
  ownership lead than an alternate OpenAlex ID alone. The canonical cluster-to-person
  bridge and independent reviewer judgment are still pending. Other recovered
  authors on the same paper are not automatically verified by Kroening's page.
- **Kien Do / Episodic Policy Gradient Training**: the author's publications page
  lists the exact title and AAAI 2022 and links arXiv `2112.01853`; the official PDF
  is cached. This is a paper-specific ownership lead, not an adjudicated canonical
  crosswalk. The arXiv identifier link was observed, not separately fetched or
  asserted equivalent by a reviewer in this task.
- **Daniel Harabor / Anytime Multi-Agent Path Finding via Large Neighborhood
  Search**: the maintained bibliography lists the exact IJCAI 2021 entry and links
  `lchsk-ijcai21-amapfvlns.pdf`. Its official proceedings PDF is also cached. This
  corroborates a specific publication entry beyond the construction ORCID alias,
  but does not certify every paper attached to the provider ID.
- **Johannes Fichte**: the University of Potsdam entry for *Decomposition-Guided
  Reductions for Argumentation and Treewidth* names `Fichte, Johannes Klaus`.
  Its path explicitly identifies a DBLP record and the entry contains BibTeX;
  treat it as a bibliographic lead with possible shared upstream, not a persistent
  person ownership assertion. This matters for the three declared name forms.
- **Shu-Tao Xia**: the Chinese institutional page is accessible, but Task2B already
  inspected the English page of the same owner. A language/endpoint change cannot
  create independent gold. It is explicitly marked shared construction owner.
- **Munindar Singh and Anil Vullikanti** owner/institution pages returned 403;
  **John Dickerson**'s requested `/publications/` path returned 404. Their sampled
  official paper PDFs provide context but no automatic canonical identity proof.
  Missing owner-page evidence is not an identity error or a non-authorship label.

All retrieved PDFs were subjected to first-page layout text extraction. **No
ORCID-shaped identifier was detected in those first-page extractions.** This does
not prove no identifier exists elsewhere in the PDFs or images. Printed emails and
bylines are useful locators, but marker alignment, personal ownership and canonical
crosswalks require actual review. No printed email alone was treated as identity gold.

Formatting diagnostics include separated/hyphenated given names and provider-ID
contexts; unresolved cases include high-impact variants. The preserved Task2B
170-ID/683-position inventory supplies contrary names/ORCIDs/coauthor context.
These strings describe observed variation, not proof of provider conflation or
person equivalence. All 448 remaining variant positions stay unresolved; no new
acceptance rule or semantic reference was inferred from contextual similarity.

## Reviewer integrity and remaining work

There are **zero human reviews and zero independently adjudicated references**.
`references/references.jsonl` and `references/ai-assessments.jsonl` are actually empty.
Pending rows have null labels and `awaiting_independent_reviews`, not invented
unknown human judgments. Source extraction/inventory was performed by Codex (GPT-6,
WORK-2026-11-11-005); it creates no person-identity votes. No agent was represented
as either human teammate or as two independent reviewers. Original historical
judgments remain untouched. No semantic AI identity label was scored.

Review-ready source ledgers separate official/publisher construction overlap,
same-owner overlap and unknown provider upstream. Reviewers can use these leads
but must independently justify exact paper ownership and candidate-person mapping.
A claim can remain unknown despite successful source retrieval. The blind workspace
receives only neutral source URLs/status/locators, not mechanisms, developer
predictions or suggested labels. Sources for non-sampled diagnostic positions
remain separate packets and must not be pooled into the probability estimator.
