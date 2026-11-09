# Agent evaluation package

The graph/content freeze remains `../release-v2/freeze-v3.json`. This package adds
AI source review without changing that graph, classifier, test membership,
thresholds, old review forms or frozen analysis/figures.

- `evaluation-freeze-v1.json`: pre-review input, prompt, design and actual-context bindings.
- `reviewer-rubric-v1.md`: frozen review instructions and ledger schema.
- `sample-preservation.json`: equality of semantic sample IDs/flags/assignments and quality settings.
- `audit/`: newly generated agent-config-bound forms; old forms remain unchanged.
- `topic-completion-freeze-v1.json`: both blind topic exports hash-frozen before edge exposure.
- `completed/`: original per-channel CSVs, factual source ledgers and completion receipts.
- `completion-receipt-v1.json`: final export/ledger hashes and review-order metadata.
- `audit-results-agent.json`: AI-assessed global/per-type edge results; supplements stay separate.
- `topic-eval-agent.json`: both frozen classifiers against paper-normalized AI reference labels.
- `evaluation-limitations.md`: source reuse, evaluator scope, uncertainty and missingness interpretation.
- `structural-validation.json` and `frozen-database-verification.json`: fresh structural/hash/read-only DB checks.

See [reproduction instructions](../../docs/reproduce-agent-evaluation.md) and the
[current work record](../../docs/status.md) for commands and completed outcomes.
The old protocol/header and AGENTS capability wording describe the pre-execution
snapshot and remain unchanged because this evaluator freeze binds their bytes;
the implemented wrapper is `src/scientific_network/evaluation/agent_review.py`.

All scores are AI-assessed. Human validation was not performed; evaluator
independence and verified course accuracy are not established. Exact runtime
model/provider IDs are unknown. Wilson intervals exclude judge error and shared
model/source bias. No push, tag, publication, invitation or submission occurs here.
