# Data Licence and Third-Party Terms

Project-authored data in this repository and in the Research Trend Navigator data release (`research-trend-navigator-data-v1`) is licensed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** licence (<https://creativecommons.org/licenses/by/4.0/>).

Code in this repository is separately licensed under the **MIT License** (see [`LICENSE`](LICENSE)).

## Project-authored data (CC BY 4.0)

Unless a record or source states otherwise below, project-authored derived outputs are licensed under CC BY 4.0:

- Graph enrichment entities (`Method`, `Task`, `Dataset`) and extracted/aggregated edges (`USES_METHOD`, `ADDRESSES_TASK`, `USES_DATASET`, `APPLIED_TO`, `EVALUATED_ON`, `RELATED_TO`), plus evidence manifests and redaction metadata
- Network analysis outputs (`reports/final-exam/analysis-v2/`: small-world metrics, rankings, personalized PageRank, Leiden communities, trend tables)
- QA benchmark questions, deterministic Cypher reference answers, receipts, and evaluation result summaries (`data/manifests/qa-benchmark-v1/`, `reports/final-exam/qa-eval-v1/`, `reports/final-exam/k1-answer/`)
- AI-generated text (`community-reports.json` and LLM-generated `entity-descriptions.json` entries), explicitly labelled `"AI-generated from graph data"` or `"AI-generated from mentions"`

## Third-party data (retains original terms)

Third-party facts and excerpts keep their own licences and attribution requirements:

- **OpenAlex** (work IDs, titles, years, authorship/affiliation links, citation edges, DOIs; no abstract text in the data release): **CC0 1.0** (<https://creativecommons.org/publicdomain/zero/1.0/>).
- **ROR** (organization identifiers): **CC0 1.0**.
- **Wikidata** (organization QIDs, types, parents, countries, inception, short descriptions): **CC0 1.0**.
- **English Wikipedia** (lead excerpts in `entity-descriptions.json` where `source_kind == "wikipedia"`): **CC BY-SA 4.0** (<https://creativecommons.org/licenses/by-sa/4.0/>). Every Wikipedia-derived record carries its `wikipedia_url`, `wikipedia_revision_id`, and attribution string; reuse of those excerpts must preserve attribution and share alike.
- **AAAI and IJCAI proceedings pages**: factual bibliographic roster membership and official URLs/PDF URLs only (no PDFs redistributed).
- **Tracked v1–v4 audit/review files**: the 50 historical audit/review files bound by frozen receipts contain public AAAI/IJCAI abstract excerpts retained strictly as audit evidence (see [`docs/source-policy.md`](docs/source-policy.md)); no new abstract text may be committed, and the data release excludes all abstract text.
