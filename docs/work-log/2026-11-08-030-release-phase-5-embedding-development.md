# WORK-2026-11-08-030 — Release Phase 5 embedding development

| Field | Value |
| --- | --- |
| Status | partial (v2 built and validated; Neo4j load awaits Phase 4) |
| Recorded | 2026-11-08 12:50 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 12:04–12:50 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-2026-11-08-029](2026-11-08-029-release-phase-5-topic-test-freeze.md) |
| Git state | `main` based on `99b166f`; this Phase 5 checkpoint is committed locally |

## Objective

Continue Phase 5 on development data only while the Phase 4 Neo4j service is blocked.
Freeze an embedding classifier without examining held-out topic predictions, build and
validate graph v2, and prepare a blind topic sheet for the two reviewers.

## Changes and findings

- Added a lazy CPU Sentence Transformers implementation in
  [embeddings.py](../../src/scientific_network/nlp/embeddings.py), hash-checked
  development-only loading, threshold/delta summaries, abstention and supporting
  excerpts. The model is `sentence-transformers/all-MiniLM-L6-v2` at immutable revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; CPU-only Torch is an optional `nlp` extra.
- Froze [topics-release-v1.yaml](../../configs/topics-release-v1.yaml) at
  `tau=0.2708871364593506`, `delta=0.02`. Calibration used 13,517 papers after excluding
  all 80 pre-existing IJCAI test papers plus all 20 new AAAI topic-test papers and their
  held-out versions. Development coverage was 84.9967% (11,489/13,517). The selected
  delta yields 2,279 multi-label papers in the full development sweep. No test title,
  abstract, prediction or label was inspected before freeze.
- Inspected a deterministic sample of 30 development predictions at the frozen delta:
  27 labeled, 3 abstained and 2 multi-labeled. This was a development diagnostic, not an
  accuracy estimate. It exposed apparent semantic errors (including graph-algorithm work
  labeled graph ML, network-diffusion inference labeled generative modeling, and entity
  alignment labeled multimodal). Topic quality remains unvalidated and needs human
  annotation; generated HAS_TOPIC edges are marked `human_review_pending`.
- Added [release_topics.py](../../src/scientific_network/resolve/release_topics.py) to
  replace phrase topics, retain provenance, rederive R9/R10, validate and write graph v2.
  Graph v2 is `release-5d830ffcbdf4`; its ignored graph SHA-256 is
  `b79e456b22488ca8f753fb0884afd5c6a89afeeeaffec07d89ce83b2c5c141fb`. The tracked
  [summary](../../reports/release-v1/graph-v2-summary.json) binds it to v1 graph SHA
  `570fb4bb5b180cea30be2c7b942aeff1f2f0aef09874a29e33dcbf78334ab761`, works SHA
  `2b7f3bc15ad46398e9f55ece060536050215238355e9580d2689f00005f55047`, frozen taxonomy
  SHA `7df4f6ad223a777be91db05f3567eaac904b0deba36d84dcaac08cff5d725ee4`, quality SHA
  `66945c3ec8e2efc13cbd9234ac2d9417f60e3fda93076a6dbe43c02606e0239f`, and frozen topic
  test manifest SHA `90d01d6483d9fe84eec055e78cf17b2a8e4f26440250488fc548c510c89158d8`.
- Added [topic_review.py](../../src/scientific_network/evaluation/topic_review.py) and
  `prepare-topic-review-sheet`. The generated CSV/HTML contain all 50 frozen test papers,
  source titles/abstracts, all 16 leaf definitions, three blank label slots, labeler and
  notes fields. They contain no classifier predictions. The browser sheet downloads a
  completed CSV. Artifacts:
  [CSV](../../reports/release-v1/audit/topic-label-sheet.csv) and
  [HTML](../../reports/release-v1/audit/topic-label-sheet.html).

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis` | passed, exit 0 | required locked environment sync; it removed the optional NLP extra as expected |
| `uv sync --locked --group dev --extra analysis --extra nlp` | passed, exit 0 | restored pinned NLP dependencies for calibration/build |
| `uv run research-network release-topic-graph-v2 --output-dir data/processed/release-graph-v2 --summary reports/release-v1/graph-v2-summary.json` | passed, exit 0; 8m51.66s, max RSS 4,215,812 KiB, no process swaps | run timing under ignored `reports/runs/WORK-2026-11-08-030/`; graph SHA above |
| `uv run research-network validate --input data/processed/release-graph-v2/graph.json --config configs/quality-release-v1.yaml --require-size --output reports/runs/WORK-2026-11-08-030/graph-v2-validation.json` | passed, exit 0; 14.95s, structural errors `[]`, all configured gates passed | independent validation binds the graph SHA above |
| `uv run research-network prepare-topic-review-sheet --output reports/release-v1/audit/topic-label-sheet.csv` | passed, exit 0; 50 papers, 16 leaves, no predictions | both review files generated; 50 blank CSV label rows; HTML has 2,400 options (3 slots × 16 leaves × 50 papers) |
| `node --check reports/runs/WORK-2026-11-08-030/topic-review-sheet.js` | passed, exit 0 | extracted browser script syntax check |
| `uv run pytest -q -p no:cacheprovider tests/test_topic_embeddings.py tests/test_topic_review_sheet.py` | passed, exit 0; 7 passed | development leakage, abstention/excerpts, sheet and no-overwrite contracts |
| `uv run pytest -q -p no:cacheprovider` | passed, exit 0; 354 passed, 1 skipped | skip remains the empty parameterized case in `tests/test_cli.py` |
| Graph inventory | passed | 52,415 nodes; 275,438 edges; all ten relations; 124,619 factual R1–R4 edges; 14,222 inferred-topic edges; 136,581 derived edges; 16 curated taxonomy edges |
| Topic coverage | measured, not quality-scored | 11,575/13,617 papers labeled (85.0040%); 2,042 abstained; no independent accuracy/recall result |
| `docker info --format '{{.ServerVersion}}'` and Neo4j port check | not available: Docker CLI is not integrated into this WSL 2 distro; port 7689 has no listener | no Neo4j load, integrity query or replay was claimed |
| `git diff --check` | passed, exit 0 | whitespace validation |

An early ad hoc HTML assertion expected 800 `<option>` elements; the correct count is
2,400 because each of 50 papers has three selectors with 16 choices. The corrected
artifact check passed. This did not indicate an output defect.

## Decisions

Keep the D040 85% development coverage target. Choose `delta=0.02` from the development
sweep to limit secondary labels; do not interpret either coverage or cosine similarity as
semantic accuracy. Preserve topic abstention and mark model labels pending human review.
No test predictions were used to select the classifier settings.

## Open issues and limitations

Phase 4 remains blocked by Docker Desktop WSL integration; therefore Phase 5 is partial
until graph v2 is loaded into the isolated `neo4j-five-year` service, integrity queries
pass and re-import is idempotent. Topic semantic accuracy is not measured. The generated
label sheet awaits reviewer input. The graph v2 file and raw run evidence are ignored and
must be regenerated from the committed code/config/data hashes in a fresh checkout.

## Next step

Restore Docker Desktop WSL integration, start only `neo4j-five-year`, load graph v2, run
inventory and integrity queries, then repeat the load and record idempotence. Phase 5 can
close after that integration check; then continue Phase 6 analysis.

## Corrections

None.
