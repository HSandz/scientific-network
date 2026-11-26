# Public-repository hygiene scan (2026-11-26, WORK-2026-11-26-001)

Scope: the full Git history (166 commits on all refs, 2,273 paths ever committed), scanned locally.
No history was rewritten and nothing was removed. This file records findings; remediation needs a
user decision.

## Secrets: none found

| Check | Result |
| --- | --- |
| gitleaks (Docker `zricethezav/gitleaks:latest`, `git` mode, all history, redacted) | 187 `generic-api-key` hits; all are false positives: SHA-256 content hashes (180 in `qa-eval-v1/pairwise-manifest.json` `pair_key_sha256`, file-hash maps in evidence and preservation baselines) and Docker image tags carrying a git SHA (`scientific-network-api:sha-…`) |
| Pattern grep over every added line of `git log --all -p` (425 MB): private keys, AWS `AKIA…`, GitHub `ghp_`/`github_pat_`, `sk-`, `sk-ant-`, Slack `xox?-`, Google `AIza…`, Hugging Face `hf_…`, `Bearer …`, Azure `AccountKey=`/SAS/connection strings | 0 hits each |
| The real local `NEO4J_PASSWORD` and `OPENALEX_API_KEY` values from the ignored `.env` (compared without printing) | 0 occurrences in history |
| Secret-like paths ever committed (`.env`, credentials, keys, tokens) | only the three `.env.example` files; every historical version holds empty or `replace-with-…` placeholders |
| `ops/llm/*.env` | model settings only (`LLM_MODEL_FILE`, `LLM_ALIAS`, `LLM_GPU_LAYERS`, `LLM_CTX`, `LLM_PARALLEL`, `LLM_KV_TYPE`) plus pinned model hashes in comments; not secrets |
| Email addresses in content | none personal (Python decorators matched by the pattern, `example.invalid`); commit metadata carries the author's own Git address |

## Publication: corpus abstract text is in the public tree and history

`docs/source-policy.md` says the repository publishes abstract IDs, offsets and hashes, "not abstract
text" (OpenAlex metadata is CC0, but abstract redistribution is not assumed). A content scan indexed
every 10-word window (stride 10) of the 13,608 corpus abstracts and slid over every added line in
history. Any verbatim span of 20 or more words is detected. 50 files match, **all of them still in
HEAD** (none is history-only).

Files with more than 10 matching windows (audit and topic-label review sheets that show abstracts or
abstract excerpts as evidence to reviewers):

| File | Matching windows | Distinct papers |
| --- | --- | --- |
| `reports/release-v1/audit/topic-label-sheet.html` | 1747 | 53 |
| `reports/release-v3/audit/edge-review-sheet.html` | 1126 | 273 |
| `reports/release-v2/audit/edge-review-sheet-v2.html` | 1126 | 273 |
| `reports/release-v1/audit/topic-label-sheet-reviewer-B.html` | 1067 | 30 |
| `reports/release-v1/audit/topic-label-sheet-reviewer-A.html` | 1020 | 33 |
| `reports/release-v4/audit/edge-review-sheet.html` | 958 | 243 |
| `reports/release-v3/audit/edge-review-sheet-reviewer-A.html` | 892 | 221 |
| `reports/release-v2/audit/edge-review-sheet-v2-reviewer-A.html` | 892 | 221 |
| `reports/release-v1/audit/topic-label-sheet.csv` | 878 | 53 |
| `reports/release-v4/audit/edge-review-sheet-reviewer-B.html` | 748 | 194 |
| `reports/release-v3/audit/edge-review-sheet.csv` | 564 | 273 |
| `reports/release-v2/audit/edge-review-sheet-v2.csv` | 564 | 273 |
| `reports/release-v3/completed/B-topics.csv` | 535 | 30 |
| `reports/release-v1/audit/topic-label-sheet-reviewer-B.csv` | 535 | 30 |
| `reports/release-v3/completed/A-topics.csv` | 513 | 33 |
| `reports/release-v1/audit/topic-label-sheet-reviewer-A.csv` | 513 | 33 |
| `reports/release-v2/audit-single-reviewer/edge-review-sheet-v2.html` | 482 | 106 |
| `reports/release-v4/audit/edge-review-sheet.csv` | 479 | 243 |
| `reports/release-v3/completed/A-edges.csv` | 447 | 221 |
| `reports/release-v3/audit/edge-review-sheet-reviewer-A.csv` | 447 | 221 |
| `reports/release-v2/audit/edge-review-sheet-v2-reviewer-A.csv` | 447 | 221 |
| `reports/release-v4/completed/B-edges.csv` | 374 | 194 |
| `reports/release-v4/audit/edge-review-sheet-reviewer-B.csv` | 374 | 194 |
| `reports/release-v2/audit-single-reviewer/edge-review-sheet-v2.csv` | 241 | 106 |
| `reports/release-v3/audit/edge-review-sheet-reviewer-B.html` | 234 | 54 |
| `reports/release-v2/audit/edge-review-sheet-v2-reviewer-B.html` | 234 | 54 |
| `reports/release-v4/audit/edge-review-sheet-reviewer-A.html` | 210 | 54 |
| `reports/final-quality-sprint/human-member-1.html` | 156 | 14 |
| `reports/final-quality-sprint/human-member-2.html` | 156 | 14 |
| `reports/release-v3/completed/B-edges.csv` | 117 | 54 |
| `reports/release-v3/audit/edge-review-sheet-reviewer-B.csv` | 117 | 54 |
| `reports/release-v2/audit/edge-review-sheet-v2-reviewer-B.csv` | 117 | 54 |
| `reports/release-v4/completed/A-edges.csv` | 105 | 54 |
| `reports/release-v4/audit/edge-review-sheet-reviewer-A.csv` | 105 | 54 |
| `reports/release-v1/audit/edge-review-sheet.html` | 64 | 19 |
| `reports/release-v1/audit/edge-review-sheet.csv` | 32 | 19 |
| `reports/final-quality-sprint/human-member-1.csv` | 31 | 14 |
| `reports/final-quality-sprint/human-member-2.csv` | 31 | 14 |
| `reports/final-quality-sprint/luna-diagnostics.json` | 30 | 8 |
| `reports/final-quality-sprint/human-member-1-flagged-post-blind.html` | 11 | 8 |
| `reports/final-quality-sprint/human-member-2-flagged-post-blind.html` | 11 | 8 |

Incidental short quotes (≤10 windows, typically one sentence quoted by a generated answer or
description): `reports/final-exam/qa-eval-v1/raw-outputs.jsonl` (9), `reports/final-exam/rag-v1/entity-descriptions.json` (8), `reports/release-v3/completed/B-edge-check-corrections-v1.jsonl` (6), `reports/final-exam/analysis-v2/ranking/personalized-pagerank.json` (5), `reports/final-exam/analysis/ranking/personalized-pagerank.json` (5), `reports/final-exam/rag-v1/research-communities.json` (4), `reports/final-exam/qa-eval-v1/supplementary-precision.json` (1), `reports/final-exam/qa-eval-v1/supplementary-precision-manifest.json` (1), `reports/quality-v5/task2b-v1/investigation/provider-context.json` (1).

Approximately: the topic-label sheets (`release-v1/audit/topic-label-sheet*`, `release-v3/completed/*-topics.csv`)
carry near-full abstracts for 30–53 papers each. The edge-review sheets carry short evidence excerpts
for 54–273 papers each.

Not found: `chunks.json`, `texts.jsonl`, `works.jsonl`, raw OpenAlex payloads (`abstract_inverted_index`
appears only as an API `select` field), paper PDFs (the only PDFs are the project's own report
figures), raw Wikipedia dumps. Wikipedia text appears only as 231 lead excerpts in
`reports/final-exam/rag-v1/entity-descriptions.json` (≈220 characters on average), each with CC BY-SA 4.0
licence, URL, revision ID and attribution, as the source policy allows.

## Remediation options (user decision; nothing done)

1. **Keep and disclose.** Treat the excerpts as audit evidence shown to reviewers, add a notice, and
   check the AAAI and IJCAI abstract terms. No history change, but this departs from the source policy.
2. **Remove going forward.** Replace the sheets in HEAD with abstract-free versions under a new dated
   decision. Several are frozen audit artifacts whose bytes are bound by receipts (AGENTS.md), so this
   needs new versioned outputs. Earlier commits stay public.
3. **Purge history.** Run `git filter-repo --invert-paths` (or `--replace-text`) on the listed paths,
   force-push `main` and tags, ask GitHub Support to purge cached views, and have every clone
   re-cloned. This rewrites every commit SHA cited in the work log, receipts and reports.

No credential rotation is needed: no secret was found.

## Resolution (2026-11-26, D042 amendment)

User decision recorded in `docs/decisions.md` ([WORK-2026-11-26-002](../../docs/work-log/2026-11-26-002-final-non-report-fixes-release.md)): **accept and document** (Option 1). The 50 tracked v1–v4 audit and topic-review files hold abstract text or excerpts of papers whose abstracts are publicly available on the AAAI and IJCAI proceedings sites, and their bytes are bound by frozen receipts; they are kept as audit evidence with no history rewrite. **No new** abstract text may be committed, and the data release bundle (`ops/release/build-data-release.py`) excludes all abstract text.
