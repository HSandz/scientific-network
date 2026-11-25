# WORK-2026-11-25-001 — Enrichment review fixes: co-occurrence, PART_OF v2, evaluator provenance

| Field | Value |
| --- | --- |
| Status | in_progress |
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

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |

## Decisions

None yet.

## Open issues and limitations

In progress.

## Next step

Finish the four items, then stop; S1-S3 are not started in this task.

## Corrections

None.
