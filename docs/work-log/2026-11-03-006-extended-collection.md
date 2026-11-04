# WORK-2026-11-03-006 — Expanded adapters, protected splits and staged collection

| Field | Value |
| --- | --- |
| Status | partial — available-venue diagnostics finished; 14 editions unresolved |
| Recorded | 2026-11-03 12:29 +0700 (Asia/Bangkok) |
| Finalized | 2026-11-03 13:26 +0700 (Asia/Bangkok) |
| Work performed | 2026-11-03 |
| Contributor | Codex |
| Related task | [Expanded plan](2026-11-03-005-expand-conference-plan.md) |
| Git state | main; no commits or remote; all existing work remains uncommitted |

## Objective

Implement and start collection for the expanded 2023 conference scope under the
user's explicit instruction, superseding D014's pause. Protect historical inputs,
freeze supplemental samples before enrichment, and execute staged acquisition,
PDF parsing, resolution, topics, derivation and a separate Neo4j import. Record
source gaps and quality limitations without fabricating completeness or accuracy.

## Changes and findings

- Added nine source-family adapters in `collect/rosters.py`: PMLR, CVF, ACL, MLSys,
  IJCAI, RSS, KR, AAMAS and MICCAI. Kept the old NeurIPS/ICML parsers and artifacts.
- Added `collect/extended.py` with per-edition checkpoints, all-series status ledger,
  partial-edition exclusion from sampling and predecessor-preserving allocation.
  A failed/unverified edition makes discovery return 1 while preserving valid output.
- Fixed query parameter canonicalization in `SourceCache`. Empty parameter mappings
  previously dropped embedded URL queries; corrected CVF requests return full lists.
  Evidence URLs retain `?day=all`, separately from canonical cache request metadata.
- Active config: `configs/corpus-extended-v2.yaml`. Preserved original corpus/quality
  configs and historical planning registry. V1 config remains a preflight record.
- Active discovery v3: **15,738 records / 14,909 included / 829 excluded**, covering
  **17 of 31 in-year editions**. Fourteen unresolved editions and three no-edition
  series are explicit. COLT/AAMAS tracks, ACL front matter, identical CoRL DOM
  repetitions and publisher RSS XIX→2023 corroboration are documented in D015.
- Frozen v3 membership: **925 test / 470 development / 13,514 pool**. Preserved all
  **5,046 legacy assignments**, including original 120 test / 60 development and
  100 diagnostics. Selected 250 diagnostics (old 100 + 15×10); zero held-out overlap.
  V2/v3 membership bytes match; v3 corrects source provenance, not allocation.
- Active metadata v3: **245/250 acquired**, **235 abstracts**, **145 strict OpenAlex
  matches**. Five official roster/detail byline contradictions withheld. Never
  relaxed byline, ORCID or affiliation thresholds to rescue counts.
- Parsed **235 PDFs**; ten MICCAI records have no official PDF link, five failed
  acquisition. 154 papers have extracted affiliation structures. Raw inputs remain
  content-addressed and ignored; existing 100 metadata/PDF/TEI records were reused.
- Resolution: **85 researchers / 32 organizations / 38 affiliation triples**.
  Same matched provider work across records is quarantined for version review.
  Venue names are config-driven; author–paper–organization alignment remains strict.
- Separated R3 roster evidence from topic text-source evidence; classifier graph
  identity now includes its method version. Draft topics cover 85/245 papers with
  108 labels and 160 abstentions. No calibration or semantic evaluation.
- New graph **`pilot-topic-d512d7239923`**, **399 nodes / 533 edges**, **369 factual
  R1–R4 edges**, eight nonempty predicates. R9/R10 remain empty.
- Added `neo4j-extended` Compose profile/service with separate volumes, Browser7475,
  Bolt7688. Original graph stays154 nodes /211 edges on7474/7687; replay and rejected
  cross-version import leave both database content digests unchanged.
- Updated instructions, README, setup, scope, plan, roadmap, data dictionary and
  docs index. Added [workflow](../extended-workflow.md), [measured report](../../reports/extended-v1.md)
  and [version/hash metrics](../../reports/extended-v1.metrics.json). Sites v3 and
  reference snapshots remain historical publications; no Site publication this task.

## Iterations and failures retained

- Initial CLI invocation used `scientific-network` (exit2, executable absent);
  corrected to `research-network`. Source probes found connection failures and
  publisher403 responses; no access restrictions bypassed.
- Discovery v1 exposed incorrect no-edition status mapping, repeated CoRL records,
  RSS year not printed on its index and ACL front matter. V2 corrected them;
  v3 corrects query-bearing evidence URLs. Prior ledgers remain unchanged.
- Metadata v1:234 acquired /169 abstracts /136 matches; v2:245 /209 /145;
  v3:245 /235 /145. Added verified MICCAI Authors paragraphs and IJCAI/KR/RSS/ACL
  abstract selectors. Literal star in one RSS title caused OpenAlex400; replacing
  the search operator preserved strict matching and recovered that record.
- Header v1 intentionally interrupted with SIGINT (exit130) after metadata fixes;
  cached completed records remain. V2 completed; v3 replayed PDF/TEI cache against
  final metadata. V3 elapsed2.881s is cache replay, not parser throughput.
- Intermediate test failures were corrected: expected exception wording, synthetic
  roster evidence fields, required fixture Paper properties and HttpUrl comparison.
  Final72 pass. Raw logs preserve failures; fixture statistics are not project results.
- Public ORCID cache warming:453 available /3 unavailable of456 identifiers from
  acquired diagnostics. This is not a count of accepted identities. Resolver still
  checks each publication and withholds uncorroborated claims.
- A final verification rerun via dynamic execution initially hit dotenv frame
  discovery; the local helper was corrected to load the explicit `.env` path.
  Final verification passed. No credentials were emitted or changed.

## Verification

All commands ran from `/home/san/Code/scientific-network`. Raw command output is
under ignored `reports/runs/WORK-2026-11-03-006/`; essential outcomes are below.

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev`; `uv lock --check` | Both0; dependencies/lock consistent | `uv-sync.log`, `uv-lock-check.log` |
| `uv run pytest` after final code changes | **0;72 passed** | `pytest-ninth.log` (earlier logs retain failures) |
| `uv run python -m compileall -q src` | 0 | Final code compiled |
| `uv run research-network schema` | 0; ten predicates | `schema.json` |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json --output reports/runs/WORK-2026-11-03-006/synthetic-validation.json` | 0; synthetic structural check only | `synthetic-validation.json` |
| `uv run research-network discover --config configs/corpus-extended-v2.yaml --output data/manifests/extended-corpus-v3` | **1; partial scope**,17 covered,14 unresolved,3 no-edition | `discover-v3.log`; active edition ledger |
| `uv run research-network split --input data/manifests/extended-corpus-v3/corpus_manifest.jsonl --corpus-config configs/corpus-extended-v2.yaml --output data/manifests/extended-splits-v3` | 0;250 diagnostics,0 held-out overlap; all legacy roles preserved | `split-v3.log`, frozen membership/summary |
| `uv run research-network acquire --config configs/corpus-extended-v2.yaml --input data/manifests/extended-corpus-v3/corpus_manifest.jsonl --splits data/manifests/extended-splits-v3/membership.jsonl --output data/interim/extended-acquired-v3` | **1;245 acquired /5 conflicts withheld** | `acquire-v3.log`, papers/failure records |
| `uv run research-network extract --config configs/corpus-extended-v2.yaml --input data/interim/extended-acquired-v3/papers.json --output data/interim/extended-headers-v3` | 0;235 parsed,10 PDF-unavailable review,5 acquisition failures; no completeness claim | `extract-v3.log`, extraction summary |
| `uv run research-network resolve --config configs/corpus-extended-v2.yaml --input data/interim/extended-headers-v3/papers.json --output data/processed/extended-resolved-v1` | 0;85 researchers,38 triples; review queue retained | `resolve-v1.log`, base graph/summary |
| `uv run research-network classify --config configs/topics.yaml --quality-config configs/quality.yaml --input data/processed/extended-resolved-v1/graph.json --output data/processed/extended-graph-v1.json` | 0;533 edges,85 topic-covered papers; uncalibrated | `classify-v1.log`, graph/decisions/summary |
| `uv run research-network validate --input data/processed/extended-graph-v1.json --output reports/runs/WORK-2026-11-03-006/extended-validation.json` | 0; structural only | `extended-validation.json` |
| Same validator with `--require-size` and unique output `size-validation.json` | **1 expected; size/ten-type gates fail** | `size-validation.json` |
| `docker compose --profile extended up -d neo4j-extended` | 0; service healthy | `compose-extended.log` |
| `NEO4J_URI=bolt://localhost:7688 uv run research-network build --input data/processed/extended-graph-v1.json --output reports/runs/WORK-2026-11-03-006/import-v1.json` | 0;399 nodes /533 edges | `import-v1.json` |
| Same build with new `import-replay-v1.json` report path | 0;399→399 nodes,533 edges; idempotent | `import-replay-v1.json` |
| Same build directed to `bolt://localhost:7687`, new `wrong-database-probe.json` path | **1 expected; version collision rejected; no report/data write** | `wrong-database-probe.log`; database snapshots equal |
| Six `queries/02_integrity.cypher` statements on each database | 0; all twelve results empty | `verification-final.json` |
| SHA-256 checks of all graph source objects, nine protected files and legacy membership equality | 0;510 source objects valid, no changed protected files,5,046 assignments preserved | `verification-final.json`; metrics |
| `uv run python reports/runs/WORK-2026-11-03-006/check-secrets.py` | 0; configured OpenAlex/Neo4j secrets absent from438 then-eligible files | `secret-boundary.json`; final recheck recorded below |
| Independent semantic audit / held-out scoring / GDS algorithms | **Not run**; annotation and implemented evaluation/analysis absent | No accuracy or release claim |

Input/config/code SHA-256 values, source counts, methods and graph version are in
`reports/extended-v1.metrics.json`. Graph SHA-256:
`44ca2715398144d36f99ef7a04e7ee1e55f84996585470f432e54157c9065cd4`.
Metadata method `pilot-acquire-v4-source-sections`; extractor
`grobid-0.8.2-crf-xml-header-v2`; resolver
`orcid-public-work-pdf-affiliation-v3-extended-venues`; classifier
`literal-phrase-baseline-v2-text-provenance`.

## Decisions

[D015](../decisions.md) supersedes the collection pause, records additive staging,
prospective small-edition quotas, explicit track mappings, version/evidence guards
and the separate Neo4j instance. Five labels, ten predicates, original configs,
release gates, public-ORCID and exact aligned-institution requirements remain.

## Open issues and limitations

- Fourteen in-year editions remain unresolved: ICLR, AAAI, ACM Multimedia, KDD,
  WWW, SIGIR, WSDM, RecSys, CIKM, ICDM, SDM, ICRA, IROS and ICAPS. Source/probe
  limitations are in the active ledger and report; this is incomplete scope.
- Five byline conflicts, ten absent MICCAI PDF links and substantial resolution
  review remain. Accepted authorships85/1,185 (7.17%); affiliated author–paper
  pairs36/1,185 (3.04%), from38 triples. Topic coverage34.69%, below target.
- No semantic precision/recall/F1 or independent accuracy above90% established.
  Size/ten-type gates unmet; only235 PDFs parsed, not the full14,909-paper roster.
- Title grouping is conservative leakage protection, not complete alternate-version
  detection or identity resolution. Later identifier/content conflicts require review.
- Final `analyze`/`evaluate`, canonical stage Parquet exports, correction history,
  reviewed migration, annotation capacity and lecturer decisions remain pending.
- No automatic commit/push; no remote backup. All collection jobs have ended;
  three local services remain running. The staged run stops here for diagnostic
  quality/source review rather than silently scaling unreliable coverage.

## Next step

Create a new linked work entry to inspect the five official byline conflicts and
the identity/affiliation queue, preserving original evidence/decisions. Annotate
development topic examples for the expanded subfields and prioritize lawful
source adapters for the14 missing editions. Acceptance: reviewed reversible
corrections, meaningful source-family tests, new versioned outputs and unchanged
held-out IDs/gates. See [status](../status.md) and [workflow](../extended-workflow.md).

## Corrections

None. Later corrections must be dated and preserve this finalized outcome.

## Final handoff verification — 2026-11-03 13:28 +0700

Credential recheck passed for 440 Git-eligible files and both configured secrets;
no leak paths. Fourteen updated documents have no missing local links. Report
metrics agree with final database snapshots. No pipeline/cache-warming processes
remain active. These checks supplement the finalized outcome above.
