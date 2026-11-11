# Task2C — independent identity validation and candidate decision

**Decision: retain `release-identity-v5-503aafe10a31` as experimental; defer
scientific promotion.** Frozen v4 stays production. No candidate has demonstrated
superior semantic accuracy: actual human reviews/adjudicated references are absent.
This task completes evaluation engineering, bounded evidence preparation, topology
sensitivity and versioned Task3 interfaces without inventing semantic results.

## Deliverables

| Deliverable | Location |
| --- | --- |
| Framework audit and corrected estimands | [evaluation-audit.md](evaluation-audit.md) |
| Local annotation application | `src/scientific_network/quality/identity_review.py` and `identity_workspace/`; launch below |
| Annotation instructions and invented worked examples | [annotation-guide.md](annotation-guide.md) |
| Strict submission/evidence/adjudication/crosswalk contracts | [annotation-schemas.json](annotation-schemas.json); Pydantic validation in `identity_review.py` |
| Independent-source preparation | [evidence-verification.md](evidence-verification.md), `source-provenance*.json`, `evidence/` |
| Actual references and pending cases | `references/`: zero real submissions; pending rows have no labels |
| Three-way evaluation | [three-way-evaluation.md](three-way-evaluation.md), `semantic-evaluation.json`, `mechanism-evaluation.json` |
| Downstream sensitivity | [graph-sensitivity.md](graph-sensitivity.md), `graph-sensitivity.json` |
| Promotion decision | [candidate-decision.md](candidate-decision.md) |
| Task3 interface and ceiling | [task3-handoff.md](task3-handoff.md), `task3-input-manifest.json` |
| Validation/preservation | [validation-report.md](validation-report.md), `validation-receipt.json`, `preservation-receipt.json`, `artifact-inventory.json` |
| Session handoff | [WORK-2026-11-11-005](../../../docs/work-log/2026-11-11-005-identity-independent-validation.md) |

Source/scorer baseline HEAD is `ac5883e`. All three graphs and the original
sampling freeze are SHA-256-bound by `checkpoint-bindings.json`. Large source
objects, graph files, annotation bundles, raw extraction and Task3 ledgers stay
ignored. Restore exact original source/candidate bytes before offline reproduction;
a fresh API response is a new version, not restoration of this evidence snapshot.

## Use the already prepared local application

The current review-ready bundle is
`reports/runs/WORK-2026-11-11-005/review-workspace-final/`.
Distribute only each person's role directory. Run these in separate terminals or
on the respective reviewers' computers (the directory has no remote dependencies):

```bash
uv run python -m http.server 8016 --bind 127.0.0.1 \
  --directory reports/runs/WORK-2026-11-11-005/review-workspace-final/A
# A opens http://127.0.0.1:8016/
uv run python -m http.server 8017 --bind 127.0.0.1 \
  --directory reports/runs/WORK-2026-11-11-005/review-workspace-final/B
# B opens http://127.0.0.1:8017/
```

Use separate browser profiles/computers. Candidate predictions exist **only** in
the separate adjudication bundle, and its UI reveals a case's claims only after
both exports contain that case. Plain static files provide workflow separation,
not authentication against a reviewer deliberately opening other directories or
reading local storage. Preserve actual independent behavior and exported originals.
Export reviews at work breaks; the browser does not write source files automatically.

After both blind exports are frozen, validate them, then serve the adjudication
directory on a third port and import both files. The two teammates can document
consensus; no invented third reviewer is needed. Preserve all uncertainties.

```bash
uv run python -m scientific_network.quality.identity_review validate \
  --evaluation reports/quality-v5/task2b-v1/evaluation \
  --submission data/annotations/task2c/review-A.json
uv run python -m scientific_network.quality.identity_review validate \
  --evaluation reports/quality-v5/task2b-v1/evaluation \
  --submission data/annotations/task2c/review-B.json
uv run python -m http.server 8018 --bind 127.0.0.1 \
  --directory reports/runs/WORK-2026-11-11-005/review-workspace-final/adjudication
```

After documenting/exporting decisions, compile them. This command accepts partial
submissions, requires both original reviews for every adjudicated case, validates
source/crosswalk schemas, and preserves AI judgments in a separate output.
Use unused paths for each compilation version; never edit submitted export bytes.

```bash
uv run python -m scientific_network.quality.identity_review compile \
  --evaluation reports/quality-v5/task2b-v1/evaluation \
  --review-a data/annotations/task2c/review-A.json \
  --review-b data/annotations/task2c/review-B.json \
  --adjudications data/annotations/task2c/adjudications.jsonl \
  --output reports/runs/task2c-human-references-v1
```

## Reproduce workspace and analyses offline

Every output directory must be unused. Original frozen files and candidate graphs
are inputs, never overwritten. The prepare command removes provider profiles and
candidate claims from the blind roles, adds neutral source leads, and includes
SHA-256-verified candidate claims only in the adjudication role.

```bash
uv sync --locked --group dev --extra analysis --extra report
uv run pytest -q tests/test_identity_validation_v5.py tests/test_identity_recovery_v5.py
uv run pytest

uv run python -m scientific_network.quality.identity_review prepare \
  --evaluation reports/quality-v5/task2b-v1/evaluation \
  --works data/interim/release-v1/works.jsonl \
  --evidence reports/quality-v5/task2c-v1/evidence/review-source-leads.jsonl \
  --candidates reports/quality-v5/task2c-v1/checkpoint-bindings.json \
  --output reports/runs/task2c-workspace-new

uv run python -m scientific_network.quality.identity_validation \
  --bindings reports/quality-v5/task2c-v1/checkpoint-bindings.json \
  --evaluation reports/quality-v5/task2b-v1/evaluation \
  --decisions data/processed/identity-candidate-v5-release-v4-final/identity-decisions.jsonl \
  --works data/interim/release-v1/works.jsonl \
  --references reports/quality-v5/task2c-v1/references/references.jsonl \
  --output reports/runs/task2c-analysis-new
```

For actual human scoring, substitute the compiler's `references.jsonl` path. A
nonempty reference file must match its compiler manifest and frozen study hash.
Complete references permit frame estimates; partial ones yield descriptive subset
results while population quality metrics/intervals stay null. All three candidate
predictions are compared on identical cases. Diagnostic categories remain separate.
Run the analysis twice with different unused output directories: report/Task3 bytes
and manifest hashes should match. The current final pair is `analysis-release/`
and `analysis-release-replay/` under this work ID; earlier runs are preserved as
intermediate engineering checks, not additional independent studies.

## Evidence replay and bounded acquisition

Offline packet rebuilding uses the three preserved provenance ledgers and their
matching new caches. It verifies every object hash and runs `pdftotext` on first
pages. `pdftotext` is required for PDF extraction (available in this environment),
not a new Python dependency. Full text is never copied into tracked reports.

```bash
uv run python -m scientific_network.quality.identity_evidence \
  --provenances reports/quality-v5/task2c-v1/source-provenance.json \
    reports/quality-v5/task2c-v1/source-provenance-unchanged.json \
    reports/quality-v5/task2c-v1/source-provenance-high-impact.json \
  --caches data/raw/identity-evaluation-task2c-v1 \
    data/raw/identity-evaluation-task2c-unchanged-v1 \
    data/raw/identity-evaluation-task2c-high-impact-v1 \
  --decisions data/processed/identity-candidate-v5-release-v4-final/identity-decisions.jsonl \
  --output reports/runs/task2c-evidence-new
```

Source acquisition itself was explicitly scoped by the three `source-request-plan*.json`
files (48 URLs total). Each request used one attempt, 18-second timeout, immutable
`SourceCache` responses, and per-host stops for 401/402/403/429. It is separate from
ordinary tests and offline replay. Reissuing failed/uncached requests can change
availability and timestamps; do not call that deterministic source restoration.
No identity labels are generated by retrieval, extraction, string observations or
source availability. Neither source consistency nor graph stability establishes
course accuracy.
