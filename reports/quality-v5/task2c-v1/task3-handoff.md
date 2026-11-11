# Task3 identity inputs and quality boundary

Use **`release-identity-v5-503aafe10a31`**, graph SHA-256
`85ff09d0a5e6a42160a3c98fad3f63941a2b412213490f4c7f744ed5e2ba4d4e`,
only as the **experimental** identity foundation. Production remains frozen v4
`release-d3c788c3114a`. Candidate-v3 is
`release-identity-v5-7e6b1a34ffa2`. Independent identity accuracy is unmeasured;
this is not a scientific promotion or permission to replace production.

The generated handoff directory is
`reports/runs/WORK-2026-11-11-005/analysis-release/task3/`. Its small hash manifest is
also retained as [task3-input-manifest.json](task3-input-manifest.json). Large public
metadata/triple/context ledgers remain ignored; reproduce with README commands.

| File | Interface |
| --- | --- |
| `accepted-authorships.jsonl` | 50,000 stable mention/paper/position decisions, canonical IDs, evidence, DOI and retained organization IDs |
| `unresolved-mentions.jsonl` | 15,507 unresolved/ambiguous official positions, reason, evidence and unaccepted paper-specific provider affiliation context |
| `accepted-affiliation-observations.jsonl` | Exact existing researcher–paper–organization observations; no affiliation enrichment |
| `handoff.json` | Input version/hash, measured coverage, exclusions/reasons and hashes of the three ledgers |

**The 80% matched-position affiliation target is unreachable through affiliation
enrichment alone.** Current identity ceiling is 50,000/65,469 = **76.372%**.
At least 52,376 correctly resolved matched positions are needed even with perfect
affiliation availability, a minimum gap of **2,376**. In reality some accepted
positions lack affiliations, so this arithmetic is a lower bound on the identity
work needed. Do not convert it into an acceptance quota or reduce identity standards.

Current affiliated positions: 47,833; accepted without affiliation: 2,167. There
are 14,930 withheld matched positions whose provider authorship has institution
context. That context does not establish person identity or constitute an accepted
triple. It is a workload indicator, not a promise of recoverable affiliations.
The handoff preserves each such position and its evidence without promoting it.

Withholding reasons (official-position denominator, mutually exclusive final
reason): 8,723 conflicting-ORCID positions; 6,263 missing provider/paper raw ORCID;
448 incompatible name variants; 38 unmatched; 21 DOI disagreement; six repeated
provider IDs; six raw-name incompatibilities; one conflicting paper/profile ORCID;
one existing-identity crosswalk collision. Refer to the machine handoff for exact
keys and joins; no person totals are inferred from these position counts.

Preserve historical retained-position organization sets and exclusions. A blank
organization list means no accepted historical affiliation support, not a positive
claim of independence or no affiliation. Do not assign every paper institution to
every author, infer past institutions from current profiles, or use an unresolved
provider as a canonical researcher. Organization collaboration requires two distinct
accepted authors with aligned organizations. Its support and rankings inherit
identity uncertainty even when the organization normalization itself is correct.

What could address the ceiling: independently establish additional person identities
and paper-specific crosswalks, retain uncertain cases, and separately validate any
new resolver iteration without reusing exposed cases as fresh gold. Task3 can improve
mapping/coverage conditional on accepted identities, but cannot resolve this upstream
denominator gap on its own. No Task3 affiliation/organization resolution is implemented
in Task2C.
