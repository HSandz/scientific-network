# Five-year release plan — 2021–2025

Decision **D018**, 4 November 2026, extends the core release from 2023 to
**2021, 2022, 2023, 2024 and 2025**. D022 (6 November 2026) subsequently authorizes necessary implementation and
staged collection, superseding the D018 execution pause. The new roster-only
config and [collection workflow](five-year-collection.md) preserve historical
2023 staging and all frozen assignments. Enrichment remains gated on cross-year
version review and prospective sample freezing.


Execution update (D023): corrected roster v2, frozen 68-paper diagnostic selection,
170 new reserved tests and a 67-record metadata tranche are now recorded. Preserve
these new test IDs in all future versions. [Measured revision 2](../reports/five-year-collection-v2.md).

## Conference and edition boundary

Retain the same 34 flagship series and track rules in [the conference policy](conference-scope.md).
The planning registry is `configs/conference-scope-2021-2025.yaml`; the original
`configs/conference-scope.yaml` remains unchanged. The new registry is not an
executable corpus config and has implementation/collection disabled.

**34 × 5 = 170 venue–year candidates**, not 170 confirmed editions. Every candidate
requires an edition decision before future acquisition. Neither a regular cadence
nor a nearby year's proceedings establishes that an edition exists. ECCV, NAACL
and COLING's historical no-2023-edition records apply only to 2023; assess their
other years independently. Record confirmed editions, no edition, inaccessible
sources, unknown tracks and unresolved records explicitly. Do not replace a
missing year with a neighboring year or omit a difficult venue without disclosure.

The official **conference edition year** defines eligibility. A proceedings volume
published later or a provider's preprint/publication date must not silently change
that year. Preserve source dates, version crosswalks and edition evidence. Source
catalog URLs are leads, not verified endpoints. Historical 2023 source availability
does not establish access or adapter support for other years. Main archival
full/short research tracks qualify under each venue's rules; verify track changes
per edition. Topic abstention does not remove an otherwise eligible paper.

## Identity, time and counting

- Keep five labels and ten predicates. Venue is a series; edition year is on Paper.
  No Year node or new relationship type is introduced.
- Count a work once in the deduplicated five-year union after source-backed version
  review, retaining one primary proceeding and all source/provider crosswalks.
  Similar titles alone never prove identity.
- Count a researcher/organization once over the union. Annual counts can overlap;
  summing them does not yield unique five-year totals. Preserve stable identifiers
  and reversible decisions.
- Affiliations remain author–paper–organization observations at publication time.
  Multiple years do not establish current employment, employment duration or a
  job move. Do not spread current profiles or a whole institution list across authors.
- Build annual and cumulative analyses from accepted paper support inside an
  explicit window. Recompute collaboration weights, distinct-paper support and
  R9/R10 thresholds for that window; filtering a union graph alone is insufficient.
  Label reused whole-snapshot weights as such in simple report filters.
- Keep factual R1–R4, inferred topics, curated taxonomy and derived counts separate.
  Release gates apply to unique five-year union counts, not every year individually
  and not a sum with repeated entities or edges.

Quality gates remain unchanged: at least 2,000 resolved core researchers, 5,000
factual edges, all ten genuinely supported predicates, independent precision/
recall/coverage and a substantive ≥10-page final report. Extra years do not
establish accuracy or justify relaxing those gates.

## Leakage-safe samples and development

Preserve all 5,046 legacy assignments and complete expanded frozen membership:
**925 test / 470 development / 13,514 pool**, including the original 120 test /
60 development papers. Keep the original 100-paper and expanded 250-paper diagnostic
sets unchanged. The D018 planning task created no new roster, sample, split or annotation.
D022 now adds a versioned roster; frozen samples remain unchanged.

Before later enrichment, reconcile the combined official roster and cross-year/
cross-venue versions. A newly found version of an old test work stays held out;
exposed development/pool papers cannot become fresh independent tests. Quarantine
ambiguous version groups and disclose any later-discovered leakage. Do not rebuild
stable IDs/frozen memberships just to accommodate a larger corpus.

Design supplemental venue–year sampling and two-reviewer annotation hours
prospectively. Do not automatically copy 60-test/30-dev or ten-diagnostic quotas
onto 170 candidates. Allocate after confirmed edition sizes/layouts and budget are
known; document small-stratum policy, selection probabilities and population
weights. Separate difficult-layout/rare-topic diagnostics from probability samples.
The 600-edge uniform final audit remains a separate frozen sample from the final
release frame; per-type supplements do not replace it.

## Temporal analysis and reporting

Plan annual/cumulative comparisons of collaboration, organization participation,
sector/topic shares and communities. Report eligible editions, paper counts,
identity/affiliation/topic coverage and unresolved sources by venue and year before
interpreting trends. Distinguish collection coverage changes from research
participation changes; use comparable windows and coverage sensitivity checks.

Citations have unequal time to accrue. Report source snapshot time, citing/cited
edition years, within-corpus boundaries and age-normalized or fixed-age comparisons
where supported. A retrospective provider snapshot is not information available
in an earlier year. Core citations require both accepted endpoints in the chosen
window; outside references remain context and cannot rescue size gates. Do not
infer causal growth or forecast success. Prediction remains optional and needs a
separate forward-time evaluation without future identities/topics/affiliations/
citation features.

## Deadline and execution readiness

The user confirmed **11 November 2026** as the deadline on 6 November. The
[execution plan](five-year-execution-plan.md) and
[170-row readiness queue](five-year-edition-readiness.csv) define dated work,
acceptance checks, cross-year safety, effort scenarios and truthful partial delivery.
The readiness-planning task performed no new edition verification or execution.
D022 now authorizes staged collection; see [measured roster results](../reports/five-year-collection-v1.md).
Deadline/capacity questions are not prerequisites.

## Work sequence after this planning revision

1. Use the confirmed 11 November deadline and preserve the proposed evaluation
   rule and scientific caveats; do not wait for further capacity answers.
2. Review the 170-candidate edition matrix and track history; plan lawful source
   routes and no-edition/unavailable states without claiming new collection.
3. Specify new executable-config versions, cross-year IDs/version review, split
   preservation, temporal derivations and migration. No implementation now.
4. Estimate metadata requests, selective PDF bytes/runtime, storage, review hours
   and costs from current diagnostics, adding uncertainty instead of multiplying
   one pilot by five. The old eight-week/16 GB assumptions are historical.
5. Obtain a later implementation/collection instruction, then implement/test offline
   before new acquisition or split freeze. Stage authorized diagnostics by source
   layout/edition before full acquisition.
6. Publish dated measured progress on the existing Site's Report tab, separate
   from Plan targets. Follow [the publication workflow](sites-workflow.md).

Current graph evidence remains 2023-only: loaded expanded graph 399 nodes / 533 edges;
reviewed local candidate 402 / 538, not imported; independent accuracy unmeasured.
These are diagnostic snapshots, not five-year results.
