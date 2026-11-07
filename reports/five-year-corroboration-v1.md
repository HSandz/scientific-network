# Frozen development corroboration — 6 November 2026

D025 / WORK-2026-11-06-005. Method `five-year-public-corroboration-v1`;
config `configs/five-year-corroboration-v1.yaml`. These are development evidence
contracts, not independent semantic accuracy or a five-year release graph.

| Measure | Measured result |
| --- | ---: |
| Frozen development papers / byline mentions | 68 / 346 |
| Input-bound printed-source overlays | 5 |
| Source-eligible papers after overlays | 49 (45 before) |
| Eligible unique ORCIDs / cached public responses | 84 / 84 |
| Accepted unique researchers | 10 |
| Previously known / new researcher IDs | 1 / 9 |
| Accepted authorship support / supporting papers | 11 / 9 |
| Accepted author–paper–organization triples | 1 |
| Typed DOI / Unicode exact title + year corroborations | 6 / 5 |
| Review queue rows | 345 |
| Original failed metadata / parser failures preserved | 1 / 2 |
| Held-out acquisition overlap / graph imports | 0 / 0 |

Five reviewed printed pages provide explicit overlays for COLT 2022 editor
contamination, two RSS 2025 GROBID failures, the MLSys 2025 abbreviated citation
byline and an IJCAI 2024 shared affiliation block. The MLSys original acquisition
stays failed; RSS originals stay parser failures. These reviews do not constitute
successful OCR or an independent annotation audit. No global author aliases added.

Complete ordered bylines, unique names within each paper, matched provider work
title/year, stable IDs and public ORCID target-publication support are required.
Typed self DOI matching is distinct from exact Unicode title with matching year;
other identifier types, part-of relationships and empty normalized titles cannot
corroborate a publication. Crosswalk conflicts are withheld. Shared provider work
and held-out-location guards found zero quarantined provider-work papers in this
sample; global canonical work resolution remains incomplete.

Only reviewed printed author/marker mappings plus exact institution matches in
that author's metadata can accept an affiliation. One COLT paper supports the
single accepted triple, for its second printed author and Universitat Pompeu Fabra.
Other TEI candidates remain review. Triple support is deduplicated before future
aggregation; no paper-wide institution union or current-profile affiliations used.

| Review reason | Rows |
| --- | ---: |
| Source title or complete ordered byline unresolved | 118 |
| No strict provider work match | 87 |
| Public ORCID target publication not corroborated | 75 |
| Missing valid stable person identifiers | 38 |
| Conflicting provider/ORCID/name crosswalk | 15 |
| Printed author-affiliation review required | 10 |
| Provider title/year or complete ordered byline unresolved | 2 |

Queue units mix unresolved author mentions and missing affiliation reviews;
345/346 is not an error rate. Lack of public ORCID works is not proof of an
incorrect identity. The conservative policy limits recall and coverage.

Verification in this task: **145 offline tests passed**. Real run and replay
return **1** for unresolved review work, with identical summaries. An additional
replay with `SourceCache.get` disabled passed without any source request.
**7,645 protected artifacts** remain unchanged; **362 source objects** verified.
**84** new public ORCID response descriptors, **zero** new OpenAlex requests.
Raw responses, per-person support tables and PDFs remain ignored/local.

Fresh read-only Docker checks before and after: GROBID alive; Neo4j original
**154 nodes / 211 edges**, extended **399 / 533**, HTTP 200. No DB writes.
The historical local candidate remains **402 / 538**, unimported.

Hashes and output identities are in [the aggregate JSON](five-year-corroboration-v1.metrics.json).
Independent semantic accuracy, recall and F1 are unmeasured. Next: review remaining
source/byline and crosswalk conflicts and printed mappings in new versions, then
freeze accepted support before isolated graph materialization. Preserve old/new
held-out IDs and do not tune against reserved tests.
