# WORK-2026-11-11-005 — Task2C independent identity validation

| Field | Value |
| --- | --- |
| Status | completed feasible engineering/evidence/analysis; human identity evaluation pending |
| Recorded | 2026-11-11T18:32:10+07:00 (Asia/Bangkok) |
| Finalized | 2026-11-11T19:00:12+07:00 |
| Contributor | Codex, GPT-6; no human reviewer impersonation |
| Git state | Initially clean main at ac5883e; implementation checkpoint 3bfec1f; local only |

## Objective

Audit the frozen Task2B scorer; implement practical independent A/B annotation,
bounded source verification, three-way sensitivity and experimental Task3 inputs.
Preserve all candidates, sources, sample membership and historical judgments.

## Changes and findings

- Scorer v2 fixes zero-TP F1 and absent-from-all-person recall, validates predictions,
  reports weighted coverage, conditional marginal intervals and paired bootstrap,
  and retains descriptive partial-reference results without population inference.
- Strict submission/evidence/crosswalk/adjudication contracts; local A/B bundles are
  blind to provider profiles, predictions and other answers. Separate adjudication
  reveals claims only after both original reviews exist; hashes preserve originals.
- Bounded public source inventory, source-owner/upstream overlap and exact locators;
  source extraction creates no identity votes. No real human submissions exist.
- Three bound checkpoints reread; topology/degree/strength recomputed, exact cached
  common-pivot betweenness verified against frozen manifests and graph values.
  Shared-assignment sensitivity and Task3 ledgers generated without graph changes.
- Recommendation: retain Task2B only as experimental; v4 stays production. No
  candidate demonstrates superior independent precision/recall. Task3 identity
  ceiling remains below the affiliation target; standards are not relaxed.
- [Complete reports and runnable handoff](../../reports/quality-v5/task2c-v1/README.md).

## Exact checks and outcomes

- `uv sync --locked --group dev --extra analysis --extra report`: exit 0; no
  dependency/lock changes. `uv run pytest -q`: **632 passed, one existing skip**,
  exit 0. `uv run pytest -q tests/test_identity_validation_v5.py
  tests/test_identity_recovery_v5.py`: **53 passed**, exit 0.
- `node --check src/scientific_network/quality/identity_workspace/app.js`: exit 0.
  Actual Chrome functional checks cover blind-save isolation, both-file gating,
  unknown state, responsive overflow and strict browser import validation.
- `identity_validation`, `identity_review prepare`, `identity_evidence` CLIs and
  separate final replays: exit 0; complete output bytes/manifests identical.
  Original frozen sampler replay exactly reproduces membership and all file hashes.
  [Exact commands/outcomes](../../reports/quality-v5/task2c-v1/validation-report.md).
- All779 earlier preservation records and148 session baseline files hash-verified;
  protected session directories retain membership. New source responses hash-checked.
  [Machine receipt](../../reports/quality-v5/task2c-v1/validation-receipt.json).
- Local design inspector at1440/768/390:0 failures,2 explained layout warnings;
  full immutable paper titles are an explicit headline-length exception. Initial
  mobile overflow fixed; remote screenshot failures replaced by local Chrome.
- Other failures retained: initial str-versus-Path inventory and unsupported design
  kind corrected;403/404 source failures remain in provenance. Raw logs/intermediates
  remain ignored under `reports/runs/WORK-2026-11-11-005/`.
- Neo4j integration/production operations not run: no import/query or graph changes.
  No corpus/topic/Explorer/Task3 resolver work, push or deployment.

## Decisions and limitations

[Task2C D040 amendment](../decisions.md). Zero independent human labels or person
crosswalks; semantic estimates stay null. Source availability and network stability
are not semantic accuracy. Exact sampled-frame restrictions and partial-reference
selection bias remain explicit. No AI identity assessments were substituted for gold.

## Next step

Distribute separate A/B directories from `review-workspace-final`, collect actual
independent exports, document crosswalks/consensus, then compile and score using
README commands on the original freeze. Keep promotion deferred until justified.

## Corrections

Historical final records unchanged. Intermediate Task2C runs remain labeled as
engineering checks; final execution paths/hashes are in `execution-artifacts.json`.
