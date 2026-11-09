# Current project status

Updated: **2026-11-09 13:31 +07:00**. Deadline: **11 November 2026**.
Plan: [D040 release plan](release-plan.md). Latest entry: [WORK-2026-11-09-007](work-log/2026-11-09-007-agent-release-review.md).

## State

- Agent evaluation, report and local packaging have been executed; review found the scorer guard below still needs correction. Human annotation is optional.
- Graph `release-9d4a6fb20f63` and [content freeze](../reports/release-v2/freeze-v3.json) are unchanged. No post-audit graph correction or classifier tuning.
- AI-assessed edge precision **176/200 = 88.00%**, Wilson 95% **82.77%–91.80%**; course point and project precision gates **FAIL**. Full results/ledgers: [release-v3](../reports/release-v3/README.md).
- Topic micro F1: embedding **.4667**, phrase **.2301**, test coverage 90%/26%. Neither reaches .95 micro precision. Topic overlap 10/10; edge overlap 39/50, kappa .1852.
- Human validation not performed; evaluator independence and verified course accuracy not established. Exact runtime model/provider IDs unknown; source reuse and judge errors limit all results.
- Resolver ignores retained `author.observed_orcids` arrays in conflict withholding; [post-audit finding](post-audit-findings.md) preserved for a separate version/new audit.
- Latest review confirms that source evidence and exactly reproduces both score JSONs. New P2 gap: scorer accepts a topic ledger without required `labels`, bypassing CSV/ledger label comparison; synthetic reproduction recorded. Current real records all contain matching labels.
- Final suite: **419 passed/1 existing skip**; schema CLI and locked sync pass. Structural/size validation and read-only Neo4j inventory/six integrity queries pass in WORK-004; earlier replay remains historical.
- [Measured report](../reports/final-report/report.md) and README complete. Final local PDF: **19 A4 pages/six figures**. ZIP: **1,320 members**, all member hashes/CRC rechecked; WORK-006 records **89 frozen/completed hashes** and zero configured-secret matches. Latest review checks 55 unique evaluation/completion bindings; all match.
- [Final package/QA receipt](../reports/release-v3/local-package-receipt-v1.json) identifies ignored PDF/HTML/ZIP paths, hashes, source checkpoint `98bc295`, visual/glyph checks and historical CSV byte differences.
- Read-only remote refs: main `05ac5d8`, no tags. GitHub HTTP504 leaves public lecturer access not_verified. No push, tag, Site publication, invitation or submission performed.

## Phase checklist

- [x] P0 Housekeeping
- [x] P1 Tooling fixes
- [x] P2 OpenAlex acquisition
- [x] P3 Graph v1 and structural validation
- [x] P4 Neo4j v1 load, inventory, integrity and replay
- [x] P5 Frozen embedding classifier, corrected graph and Neo4j replay
- [x] P6 Fresh corrected-graph analysis, figures and findings
- [x] P7 Replacement freeze and consistent review packets
- [x] Resolve pre-audit taxonomy, fallback-scoring and reviewer-export issues
- [x] Independently review the corrected pre-audit package
- [x] Adopt agent workflow; implement/test provenance and freeze evaluator inputs
- [x] Complete and score source-backed agent edge/topic reviews
- [x] P8 Measured final report and README
- [x] P9 Local PDF and submission packaging (external delivery pending)
- [x] Review completed evaluation/report/package (WORK-007; findings open)

## Next local work

Require topic-ledger `labels` in the scorer, add a missing-field regression and confirm unchanged real results. This review preserved code and frozen artifacts. Known graph quality failures need a separately versioned correction/new audit; no post-audit tuning or silent replacement.

## Remaining facts and external delivery

Real student names/IDs/actual contributions, course AI-use rules and lecturer access remain unavailable. The local bundle is a submission draft until those facts are reflected in a new render. Follow [the checklist](local-submission-checklist.md); push/tag/Site publication/invitation/submission require separate explicit authorization. Human annotation is optional; the scorer fix above is feasible agent work.
