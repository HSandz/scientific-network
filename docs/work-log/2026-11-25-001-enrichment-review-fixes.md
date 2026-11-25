# WORK-2026-11-25-001 — Enrichment review fixes: co-occurrence, PART_OF v2, evaluator provenance

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-25 10:34 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-25 |
| Contributor | Claude (Sonnet 5.5), Claude Code CLI |
| Related task | [WORK-2026-11-24-004](2026-11-24-004-enrichment-e1-e4.md) |
| Git state | `main` at `0f37097` (history was rewritten and force-pushed upstream); line-ending noise in 15 v3/v4 CSVs and the user's `docs/README.md` / prompt file left untouched |

## Objective

Four reviewer items before network analysis: (1) method-task-dataset connections through shared papers, (2) PART_OF re-evaluation with
the Wikidata statement shown, (3) record the real evaluator model, (4) preserve the evaluator evidence. The frozen relation rule is not changed.

## Changes and findings

- **Item 4/3 first (the scratchpad can be wiped)**: it already had been. The evaluator working directories under the session scratchpad
  (packet and guideline copies, answer copies, `run.log`, `last-message.txt`) no longer existed. Preserved instead: the 7 Codex rollout logs
  (copied from `~/.codex/sessions/2026/11/25/`), the 8 Claude subagent transcripts (from `~/.claude/projects/.../subagents/`), the frozen packets,
  the committed answers and a guideline copy, archived under ignored `reports/runs/WORK-2026-11-24-004/eval/`; hashes and IDs in
  [`evaluator-evidence.json`](../../reports/enrichment-v1/audit/evaluator-evidence.json) (`enrich/evidence.py`). The lost files are listed in the
  run-info correction. Models read from the logs: channel B `gpt-6.2-sol` via provider `9router` (Codex CLI 0.171.0), channels A and C
  `claude-opus-5-5`. Recorded as a dated correction in `reports/enrichment-v1/audit/run-info.json` (original text unchanged).
- **Item 1, shared-paper connections** (no new predicate or threshold): `enrich/cooccurrence.py` (`CooccurrenceIndex.partners`,
  `distribution`), CLI `enrich cooccurrence`, `queries/enriched-{method-task,method-dataset,task-dataset}.cypher`, tests on a synthetic
  fixture. Measured on `enriched-c0f7d1dd4abd` ([`cooccurrence.json`](../../reports/enrichment-v1/cooccurrence.json)): pairs with at least
  1 / 2 / 3 / 5 shared papers: Method-Task 2,864 / 207 / 56 / 14; Method-Dataset 1,466 / 114 / 25 / 4; Task-Dataset 923 / 289 / 136 / 28.
  Methods with a Task partner: 719 of 948 at one paper, 83 at two; Tasks with a Method partner 602 of 673 at one, 112 at two. So the connection
  is usable at one shared paper (with the paper shown as evidence) but thin at two or more. Top pairs: graph neural networks / node
  classification 14; 3D Object Detection / nuScenes 14; semantic segmentation / Cityscapes 14. Duplicate-looking nodes remain (for example
  ResNet and ResNet-50) because `entity_key` keeps "resnet" and "resnet 50" apart; not changed here. The Cypher files were **not run**: Docker is not
  available in this WSL distribution now, so only the Python function and its tests ran. Specification §4.3 has a dated note.
- **Item 2, PART_OF v2** (`enrich/part_of_v2.py`, CLI `audit-partof-v2`): the same 50 frozen items with the Wikidata property (P749/P361),
  both QIDs and labels, the statement item URL and the per-statement raw-store response SHA-256 and retrieval time. Packets and
  [receipt](../../reports/enrichment-v1/audit/partof-v2-receipt.json) were committed (`4ef4342`) before any v2 judgment; the receipt says v1
  is superseded only for this axis, that v2 was created after the v1 results were seen, and that only the evidence shown changed. Side finding: the graph's PART_OF
  evidence records carry one aggregate hash of all SPARQL responses, not a per-statement hash; the v2 packets use the per-statement hash
  found by re-reading the raw store (graph left frozen). Judged by A (fresh `claude-opus-5-5`), B (fresh `codex exec`, `gpt-6.2-sol` via `9router`)
  and C for the 3 disagreements (`claude-opus-5-5`); the building session did not judge.
  **Result**: v1 0.694 [0.531, 0.820] (25/36, 14 unclear; 0.500 with unclear as incorrect) against v2 0.720 [0.583, 0.825] (36/50, 0 unclear);
  raw A/B agreement 0.94, kappa 0.8485. The packet defect explained the unclear verdicts, not the weak precision: the 14 incorrect v2 verdicts are
  real data problems in Wikidata `P361`/`P749` targets: stock indices and company lists (S&P 500, Dow Jones, IBEX 35, Forbes Global 2000, a Gaza war company list; 7),
  reversed direction (UBC to VCHRI, a faculty to its university; 2), and joint or former memberships (ParisTech, a ComUE, Inria, CPE Lyon, Sōkei; 5). Target 0.80 not met on either packet.
  The v2 section in `quality.md` / `quality.json` is supplementary; v1 stays beside it and no other axis changed.
- **Corrections recorded** in `run-info.json` and appended to `quality.md` (rendered from `run_info.corrections`), v2 runs included.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run pytest -q` | passed, 715 passed / 1 skipped, exit 0 | terminal, after the last code change |
| `uv run research-network enrich cooccurrence --graph ... --output reports/enrichment-v1/cooccurrence.json` | exit 0 | `cooccurrence.json`, graph `enriched-c0f7d1dd4abd` |
| `enrich audit-partof-v2 ...` | exit 0; 50 items, 0 without a raw statement hash | `partof-v2-receipt.json`, packets hashes `d7d1498885...` (A), `c0fa024542...` (B) |
| `enrich score-audit ... --run-info reports/enrichment-v1/audit/run-info.json` | exit 0 | `quality.json`, `quality.md` |
| `enrich.evidence` manifests (v1 and v2) | exit 0; 54 and 20 files hashed | `evaluator-evidence*.json` |
| Cypher files `queries/enriched-*-*.cypher` | **not run**: Docker unavailable in this WSL distro | read-only; Python equivalent tested |

## Decisions

No new D042 decision: the relation rule, thresholds and sample are unchanged. Co-occurrence is a read-only application query, recorded as a dated
note in specification §4.3. Candidate v2 relation and PART_OF rules (below) would each need a dated amendment, development-only tuning and a new E4 sample.

## Open issues and limitations

- Co-occurrence is thin at two or more shared papers (83 of 948 Methods have a Task partner at two papers); at one paper it covers 719 Methods but each connection rests on a single paper.
- `ResNet` and `ResNet-50` stay separate nodes (entity key); not addressed.
- PART_OF precision is 0.72 even with the statement shown (target 0.80). Excluding `P361` targets that are indices or lists, and reversed directions, would remove most
  errors but is a new rule (future decision, not done).
- The evaluator working directories from the v1 audit were already wiped; run.log, last-message.txt and packet-time guideline copies for v1 are lost (listed in `run-info.json`).
  v2 evidence was archived at once.
- Isolation of A/B/C is by working directory and instruction, not a hard barrier; A and C are one model family. Wilson intervals exclude evaluator error.
- Cypher query files unrun (no Docker now).

## Next step

S1-S3 network analysis on `enriched-c0f7d1dd4abd` (not started here); when Docker is available, run the three `queries/enriched-*-*.cypher` files against
`neo4j-enriched` for one known pair (graph neural networks / node classification should return 14 papers).

## Corrections

None.
