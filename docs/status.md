# Current project status

Updated: **2026-11-04 (Asia/Bangkok, UTC+07:00)**.
Latest task: [WORK-2026-11-04-003 — native Report integration](work-log/2026-11-04-003-native-site-report.md).
**Current instruction: 2021–2025 planning, documentation and Site updates only.
Pipeline implementation and research collection are paused (D018).**
The [five-year plan](five-year-scope.md) retains 34 series and 170 venue–year
candidates requiring edition verification, not 170 confirmed editions. No new
five-year executable config, roster, sample, collection or graph has been created.

Planning registry: `configs/conference-scope-2021-2025.yaml`. All historical
executable configs, frozen memberships, source data, graphs and measured reports
are preserved. The existing public Site is published as **version 5**, renamed **AI Research
Network — Plan & Report (2021–2025)**, with **Plan** and **Report** tabs (D019/D020). The Report has native graph, charts, filters,
coverage, evidence inspection and exports; no iframe or separate embedded page.
[Open Site](https://ai-research-network-plan.hazy-tern-8113.chatgpt.site),
[publication receipt](reference/sites-native-publication-2026-11-04.json); [publication workflow](sites-workflow.md), [publishable report](../reports/site-report.md).

Task 003 checks: **97 offline tests passed freshly**; schema and synthetic
structural validation pass. Native graph renders 399 nodes / 533 edges; all four
projections, conference/search filters, evidence, charts, JSON/CSV export,
print-event restoration and Plan controls checked. Browser checked responsive
layouts at 1440/768/390px, pointer tab switching, keyboard navigation and desktop/
mobile screenshots. Initial hidden-browser timeouts resolved by selecting its tab.
Live version 5 verified: zero embedded documents, no console errors, 20 preserved
Plan sections, native controls and correct graph version. Exact original payload,
Plan source and all 5,713 protected files unchanged. No collection or DB writes.

Historical 2023 evidence: [review results](../reports/evidence-review-v1.md),
[machine summary](../reports/evidence-review-v1.metrics.json),
[commands](evidence-review.md), [history](work-log/README.md).

## Latest measured candidate — historical 2023 evidence (task 001)

- All **250 diagnostic metadata records acquired**, 240 abstracts, 145 strict
  OpenAlex matches. Acquisition v4 reuses 245 successful historical records.
- After the user started containers, GROBID extraction v5 parsed **240 PDFs**;
  ten MICCAI records lack official PDF URLs. The failed-service v4 pass is preserved.
- Reviewed five byline conflicts: **three core admissions, two withheld** for
  contradictory PDF author order/count. No identity aliases or threshold relaxation.
- Candidate **`pilot-topic-7e3c90189547`**, **402 nodes / 538 edges**: 248 Paper,
  85 Researcher, 32 Organization, 20 Topic, 17 Venue. **372 factual R1–R4** edges,
  110 inferred topics, 16 taxonomy, 40 derived. Eight predicates nonempty.
- Original **718 queue rows** triaged without graph overrides. Stored technical
  checks pass for 85 identities / 38 affiliation triples, with 813 cached objects
  checked. Five printed-source observations corroborate existing mappings;
  **no affiliation triple IDs added or removed**. Candidate queue: 723 rows.
- **97 offline tests passed in task 001**; its structural validation and lock consistency
  passed. `--require-size` correctly returns 1. Final candidate's 513 source objects,
  20 protected files and all 5,046 legacy assignments verified; zero held-out overlap.
- These are agent development checks. **Independent semantic accuracy is unmeasured**;
  no precision, recall or F1 release claim. See [D017](decisions.md#d017--input-bound-development-source-review-2026-11-04).

## Historical service checks and visual output

In task 001 (4 November, 01:14 +07:00), GROBID 8070 and Neo4j HTTP 7474/7475 return 200. Both databases pass six integrity
queries and have the same content digests as task 006, checked then, not rerun during planning task 002:

| Output | Version / contents |
| --- | --- |
| Neo4j original, Browser 7474 / Bolt 7687 | `pilot-topic-0bb7f11a404e`; 154 nodes / 211 edges |
| Neo4j expanded, Browser 7475 / Bolt 7688 | `pilot-topic-d512d7239923`; 399 nodes / 533 edges |
| [Offline HTML report](../reports/extended-v1.html) | Previous expanded graph, 399 / 533; task 007 browser checks |
| Local candidate, not imported | `pilot-topic-7e3c90189547`; 402 / 538 |

No database writes in task 001 or planning task 002. The loader rejects replacement versions sharing
entity IDs; safe migration or an isolated instance is required before candidate
loading. The HTML's matching original metrics remain unchanged. Do not claim it
shows the new candidate. No collection jobs remain running.

## Historical 2023 scope and frozen samples

D015 authorized the historical expanded 2023 collection. Current D018 pauses
execution and expands the planned target to 2021–2025. Historical scope was
**34 series / 31 in-year 2023 editions**; preserved executable config
`configs/corpus-extended-v2.yaml`. **17 covered / 14 unresolved**, plus ECCV/NAACL/
COLING without a 2023 edition. Ledger: 15,738 records, 14,909 included / 829 excluded.
This is partial conference coverage; see [the original expanded report](../reports/extended-v1.md).

Frozen membership: **925 test / 470 development / 13,514 pool**; all 5,046 legacy
assignments, including 120 test / 60 development, preserved. Diagnostics remain
250 (original 100 plus ten per 15 new venues). Held-out samples remain unannotated.
Legacy configs, data, reports and original Sites snapshots are preserved.

## Active local artifacts

| Artifact | Path |
| --- | --- |
| Roster / edition ledger | `data/manifests/extended-corpus-v3/` |
| Frozen membership | `data/manifests/extended-splits-v3/` |
| Metadata / extraction | `data/interim/extended-acquired-v4/`, `extended-headers-v5/` |
| Original queue triage | `data/processed/extended-review-v1/` |
| Reviewed source ledger | `data/manifests/reviews/source-review-v2.json` |
| Candidate base graph / queue | `data/processed/extended-resolved-v3/` |
| Candidate topic/derived graph | `data/processed/extended-graph-v2.json` and sidecars |
| Current raw checks | `reports/runs/WORK-2026-11-04-001/` (ignored) |

Earlier artifacts remain historical diagnostics; source-review-v2 supersedes the
byline-only review-v1 ledger, and resolved-v2 is a preliminary candidate.

## Next planning work and limits

1. Review the five-year edition matrix, track history and lawful source routes;
   confirm actual deadline, annotation capacity and lecturer interpretation.
2. Specify cross-year versions/leakage protection, venue–year sampling and
   annual/cumulative support with citation-age controls. Preserve frozen test IDs;
   do not implement or create new splits under the current request.
3. Re-estimate runtime/storage/API costs and reviewer hours, then wait for a later
   explicit pipeline implementation/collection instruction.
4. Keep the existing Site's Report tab updated after material finalized tasks
   using dated measured artifacts and verified publication receipts (D019).

Development identity/affiliation adjudication, two PDF/byline conflicts, topic
calibration and safe graph migration remain future tasks after authorization.
The 2023 candidate labels 87/248 papers (35.08%); 161 abstentions. Author resolution
85/1,206 (7.05%); affiliated pairs 36/1,206 (2.99%). These are not five-year metrics.

Size, all-ten-type, coverage and independent-audit release gates remain unmet.
`analyze`/`evaluate`, complete canonical Parquet exports and broader identity
adjudication remain planned. GDS compatibility is separate. Lecturer interpretation,
member names/IDs, deadline, annotation hours and code license remain unspecified.
Git is on `main` without commits or a remote backup. Historical Sites version 3
and reference snapshots remain unchanged. Current publication outcome is recorded
in task 003 and its new receipt; no new research data was collected.
