# Sources and collection policy

## Expanded source families (D022 staged collection)

The [2021–2025 scope registry](five-year-scope.md) retains PMLR/OpenReview, CVF/ECVA, ACL
Anthology, AAAI/IJCAI, ACM/IEEE/SIAM/Springer and dedicated robotics/reasoning
proceedings. All 170 venue–year candidates require independent edition/track
verification; registry catalog URLs are leads, not verified edition rosters.
D022 authorizes staged official source/roster collection under a new executable
config; it supersedes the D018 execution pause. Verify edition/track IDs, metadata
routes, rights, quotas and lawful access per family. Catalog access alone is not
roster verification. Restricted publisher access is recorded as unavailable,
without bypassing access controls. See [collection workflow](five-year-collection.md).

The two venue rows below describe the existing pilot; OpenAlex and scholarly
search services enrich claims and cannot independently define corpus membership.

## Authority by claim

| Source | Role | Limitation |
| --- | --- | --- |
| [NeurIPS 2023 proceedings](https://proceedings.neurips.cc/paper/2023) | Acceptance, main-track roster, byline, abstract, PDF | Exclude Datasets and Benchmarks; proceedings co-location is not main-track evidence |
| [ICML 2023 / PMLR 202](https://proceedings.mlr.press/v202/) | Official ICML roster and records | Exclude non-paper material; preserve official version |
| [OpenAlex authorships](https://help.openalex.org/data/authorships/) | Work matching, authorship-specific affiliation strings, references | Provider IDs/matches are not ground truth; verify full bylines/truncation |
| Official paper PDF | Printed author–affiliation mapping and explicit references | Parse selectively; verify markers and disputed mappings |
| [Public OpenReview records](https://docs.openreview.net/) | Linked identifiers, public keywords and corroborating identity | Current profile affiliation is not historical paper affiliation |
| [ROR affiliation matching](https://ror.readme.io/docs/api-affiliation) | Organization names, aliases and canonicalization candidates | Prefer documented chosen match; review ambiguity/hierarchy |
| Wikipedia and organization sites | Optional descriptions and manually checked aliases | Enrichment only; not needed for graph size |

No Google Scholar scraping dependency or paid service is required. Recheck
[OpenAlex authentication](https://help.openalex.org/api/authentication/) and
[pricing/access guidance](https://help.openalex.org/access/pricing/) before
collection; the plan's November 2026 access assumptions can change.

## Acquisition contract

Enumerate the full official roster before enrichment. Record URL, source record,
timestamp, content hash, source terms/license if supplied, parser version and
terminal status. Verify work matches through identifiers or combined title/year/
venue/byline evidence; title similarity alone is insufficient.

Cache immutable responses, resume completed records, honor retry timing, bound
retries with jitter, use source-specific concurrency and stop at usage limits.
Distinguish access restriction, missing fields, parser failures and ambiguous
matches. Preserve the official ledger record through enrichment failure.

GROBID [service APIs](https://grobid.readthedocs.io/en/latest/Grobid-service/):
`processHeaderDocument` for headers and `processFulltextDocument` when references
or disputed alignments need it. Disable/record external consolidation. Preserve
TEI/page/marker locators, raw and normalized fields, and technical/name glyphs.

## Rights and release

Use public research evidence relevant to this course project. Public availability
does not itself establish redistribution permission. Keep credentials, unnecessary
personal/profile data and unredistributable full texts outside source control.
Provide acquisition/rebuild instructions for restricted inputs. Record unknown
source-license status explicitly; do not invent a license or assume one provider's
license covers official PDFs. Choose the repository's code license separately.

Core citation analysis is core → core. Keep unmatched/external references in staging;
an optional one-hop context layer is separately labeled and cannot satisfy core size.
Never recursively acquire external authors/affiliations/references by default.
