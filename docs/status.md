# Current project status

Updated: **2026-11-11 +07:00**. Plan: [D040](release-plan.md),with
[user-authorized v5 candidate amendment](decisions.md).
Latest: [WORK-2026-11-11-003](work-log/2026-11-11-003-quality-v5.md).

## Current phase checklist

- [x] Historical v4 graph,source snapshots,AI evaluation and package preserved.
- [x] Historical Site/Explorer delivery remains separate from this task.
- [x] V5 Task1 baseline source/data/pipeline audit and issue priorities.
- [x] Baseline hashes,raw object equality and structural validation checked.
- [x] Audit tests and full repository suite:533 passed,one existing skip.
- [ ] V5 Task2 conservative mention resolver and regression tests.
- [ ] Isolated candidate,deterministic reproduction and v4 comparison.
- [ ] Final identity implementation/validation report and handoff.
- [ ] Personal/course facts and final course submission.

## Findings and boundary

[Baseline audit](../reports/quality-v5/baseline-audit.md),
[machine census](../reports/quality-v5/baseline-audit.json),
[priorities](../reports/quality-v5/issue-inventory.csv).
Current builder state shadowing confirmed;frozen v4 uses a different historical
path. Singleton DOI disagreements and missing identifiers require abstention.
Paper raw identity evidence is sparse;aggregate ORCID arrays cannot assign people
to papers. Independent identity precision/recall remain unmeasured.

No source collection,database writes,production/Explorer changes,push or deploy.
Historical [v4 evidence](../reports/release-v4/README.md) remains frozen.
AI-assessed precision is not independent human validation or verified course accuracy.
Next: implement the separately versioned identity candidate from Task1 findings.
