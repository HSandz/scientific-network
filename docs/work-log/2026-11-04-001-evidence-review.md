# WORK-2026-11-04-001 — Byline and identity/affiliation evidence review

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-04 00:42 +07:00 (Asia/Bangkok) |
| Finalized | 2026-11-04 01:14 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-04 |
| Contributor | Codex |
| Related task | [Task 006](2026-11-03-006-extended-collection.md); [task 007](2026-11-03-007-html-report.md) |
| Git state | main; no commits or remote; existing repository files untracked, preserved |

## Objective

Review five withheld byline conflicts and the identity/affiliation queue. Record
reversible evidence-backed decisions and implement source-handling fixes where
justified, with versioned outputs and unchanged held-out assignments/thresholds.
The user started Docker during the task and authorized needed service work.

## Changes and findings

- [Acquisition](../../src/scientific_network/collect/acquire.py) now preserves
  Unicode name tokens, prefers a unique ACL publication byline consistent with the
  frozen roster, records citation-name differences, and supports `--previous`
  with frozen manifest/membership and exact roster checks. Reused 245 successes;
  recovered all five metadata failures. No name-only merge/transliteration alias.
- [Extraction](../../src/scientific_network/preprocess/extract.py) retains PDF hash
  and byte count even if the local parser fails. Initial v4: 235 parsed / 15 review
  while GROBID was unavailable. After Docker started, v5: 240 parsed / 10 review;
  remaining MICCAI records lack official PDF URLs. Existing cache bytes preserved.
- [Offline evidence review](../../src/scientific_network/resolve/review.py) and
  CLI `review` preserve the original queue, stable hash/ordinal decision IDs and
  source references without graph overrides. All 718 rows triaged; 85 accepted
  identity / 38 affiliation technical checks pass, 813 distinct objects checked.
- Inspected the five recovered PDFs: EACL 152, EMNLP 401 and 536 retain publication
  bylines; EACL 280 and MLSys remain withheld for PDF order/count disagreements.
  Recovering a source record does not force researcher identity acceptance.
- [Resolution](../../src/scientific_network/resolve/pilot.py) accepts input-bound
  source-withholding decisions and reviewed printed affiliations. Decisions bind
  input/record/PDF hashes, position/name and locator. Affiliations still require
  accepted ORCID identity and exact institution on that author's provider record.
  Repeated support merges into deterministic triples.
- Reviewed five printed mappings in EACL 164/171. GROBID had repeated combined
  institution lists under several authors, generating spurious review candidates.
  **The five correct mappings were already accepted** by the exact provider
  intersection. The new ledger corroborates them directly; zero triple IDs added
  or removed. It does not close all suspect queue rows or add five new affiliations.
- New [source ledger](../../data/manifests/reviews/source-review-v2.json),
  [review report](../../reports/evidence-review-v1.md),
  [machine summary](../../reports/evidence-review-v1.metrics.json),
  [workflow](../evidence-review.md), README/roadmap/status updates and regression tests.
- Candidate graph: **402 nodes / 538 edges**, 248 papers, 85 researchers,
  32 organizations, 20 topics, 17 venues; 372 factual, 110 inferred-topic,
  16 taxonomy and 40 derived edges. 38 triples; 723 mixed-unit review rows.
  Eight predicates nonempty; 87 topic-labeled papers, 161 abstentions.
- Read-only checks verified both live Neo4j databases and GROBID. No database writes:
  original 154/211 and expanded 399/533 retain exact prior content digests. Candidate
  stays local because D011 rejects replacement versions sharing entity IDs.

## Verification

All commands ran from `/home/san/Code/scientific-network`. Raw outputs are under
`reports/runs/WORK-2026-11-04-001/` (ignored); summaries below are portable.

| Command/check | Outcome / exit code | Evidence |
| --- | --- | --- |
| `uv run pytest -q` | 97 passed / 0; earlier suites 89 and 94 passed | `pytest-final.txt`; meaningful identity-gated triple, repeated-support, Unicode, order, hash and held-out cases |
| `uv run research-network review --input data/interim/extended-acquired-v3/papers.json --headers data/interim/extended-headers-v3/papers.json --graph data/processed/extended-resolved-v1/graph.json --queue data/processed/extended-resolved-v1/review-queue.json --manifest data/manifests/extended-corpus-v3/corpus_manifest.jsonl --splits data/manifests/extended-splits-v3/membership.jsonl --cache data/raw/source-cache --config configs/corpus-extended-v2.yaml --output data/processed/extended-review-v1` | 0; 718 rows, 123 accepted-claim checks passed, 813 objects | `review-v1.log`; output summary |
| `uv run research-network acquire --config configs/corpus-extended-v2.yaml --input data/manifests/extended-corpus-v3/corpus_manifest.jsonl --splits data/manifests/extended-splits-v3/membership.jsonl --previous data/interim/extended-acquired-v3/papers.json --output data/interim/extended-acquired-v4` | 0; 250 acquired, 240 abstracts, 145 work matches, 245 reused | Acquisition v4 summary |
| `uv run research-network extract --config configs/corpus-extended-v2.yaml --input data/interim/extended-acquired-v4/papers.json --output data/interim/extended-headers-v4` | 0 with partial results: five local parser failures, ten missing PDFs | Preserved v4 diagnostic |
| Same extraction with `--output data/interim/extended-headers-v5` after Docker started | 0; 240 parsed / 10 review, 159 papers with header affiliations | v5 summary; parser recovered all five |
| `uv run research-network resolve --config configs/corpus-extended-v2.yaml --input data/interim/extended-headers-v5/papers.json --decisions data/manifests/reviews/source-review-v2.json --output data/processed/extended-resolved-v3` | 0; five observations applied, two core withholds; 38 existing triples | `resolve-v3.log` |
| `uv run research-network classify --config configs/topics.yaml --quality-config configs/quality.yaml --input data/processed/extended-resolved-v3/graph.json --output data/processed/extended-graph-v2.json` | 0; 402 nodes / 538 edges | `classify-v2.log` |
| `uv run research-network validate --input data/processed/extended-graph-v2.json --output reports/runs/WORK-2026-11-04-001/validation-v2.json` | 0, no structural defects | `validation-v2.json` |
| Same validate with `--require-size --output reports/runs/WORK-2026-11-04-001/size-validation-v2.json` | **1 expected**: researcher, factual-edge and ten-type targets unmet | `size-validation-v2.json` |
| `uv lock --check` | 0; no dependency changes | `uv-lock-check.log` |
| `uv run python reports/runs/WORK-2026-11-04-001/verify-current.py` | 0; 513 candidate source hashes, 20 protected hashes, all 5,046 legacy assignments unchanged, no held-out groups acquired | `verification-current.json` |
| Read-only `queries/02_integrity.cypher` on Bolt 7687 and 7688; canonical property content digests | Six queries each return zero violations; both digests match task 006 | `verification-current.json`; no writes/import performed |
| HTTP checks GROBID 8070 and Neo4j 7474/7475 | All 200 | `verification-current.json` |
| Configured credential bytes against Git-eligible files, using `dotenv_values` and `git ls-files --cached --others --exclude-standard -z` | 0; no leaks | `secret-boundary.json`; no credentials logged |
| Local Markdown link check on nine edited documentation/report files | 0; no missing local targets | `docs-links.json` |
| Independent semantic audit, calibration, GDS, candidate DB import, refreshed HTML browser check | **Not run**; outside this evidence-review iteration | Existing HTML preserved; no new accuracy claim |

Versions: acquire `pilot-acquire-v5-visible-byline-unicode` (five new records;
245 historical records reused); extract `grobid-0.8.2-crf-xml-header-v2`;
resolve `orcid-public-work-pdf-affiliation-v4-source-review`;
review `frozen-diagnostic-evidence-review-v1`; classifier
`literal-phrase-baseline-v2-text-provenance`.
Base graph `pilot-cdbd7165f817`; final candidate `pilot-topic-7e3c90189547`, SHA-256
`b78ecb704e356847b1066e01c70da5f1875f3f987bf1a0f57051b702765aa144`.
All input/config/code hashes: [machine summary](../../reports/evidence-review-v1.metrics.json).

## Decisions

[D017 — Input-bound development source review](../decisions.md#d017--input-bound-development-source-review-2026-11-04).
No corpus/schema/release-gate changes. D011 database version guard preserved.

## Open issues and limitations

Two PDF/byline conflicts remain; 14 editions unresolved; ten MICCAI PDF URLs absent.
Identity coverage is still 85/1,206 official authorships (7.05%); 36/1,206 affiliated
pairs (2.99%). No independent precision, recall or F1; topic baseline uncalibrated.
Queue counts mix claim units and cannot serve as error rates. The 718-row original
queue is preserved, not treated as fully adjudicated. All 925 test assignments
remain untouched. Candidate not imported; HTML/database snapshots remain graph-v1.
No jobs running. Git still has no commit or remote backup. No Site republished.

## Next step

Adjudicate the two source-version conflicts and development identity/affiliation
claims using [the review ledger](../../data/manifests/reviews/source-review-v2.json)
and original queue triage, keeping test groups untouched. Acceptance: every
promoted claim has source/hash/locator and stable identity corroboration; preserve
withheld status otherwise. Plan reversible backed-up graph migration before loading
candidate graph-v2; verify reconciliation/idempotence and then refresh HTML.

## Checkpoint — 2026-11-04 00:53 +07:00

All five cached official records parse under the corrected visible ACL byline/Unicode policy. Metadata acquisition v4 reused245successful diagnostic records and recovered all five failures, preserving the same250selected IDs. Review718records:380ORCID publication gaps,187identifier gaps,100work-match gaps,40institution strings,11header alignment gaps. Cached PDFs/TEI show possible cross-author affiliation swaps in EACL; do not promote aliases/ambiguous mappings. Docker executable is absent and localhostGROBID8070/Neo4j7475are unreachable today. Extraction of the five recovered records is running with immutable cache; failed local parser requests must remain explicit. No database mutation performed.

## Corrections

2026-11-04 01:14 +07:00: the checkpoint's unavailable-service observation described
that earlier moment. After the user started containers, both databases/GROBID were
reachable and extraction v5 recovered the five PDFs. Direct comparison also shows
that the five reviewed affiliation mappings were already accepted: combined TEI
lists introduced extra candidates, rather than replacing all correct support.
The final results above distinguish source corroboration from new triples.
