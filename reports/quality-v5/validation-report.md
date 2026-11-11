# Validation and evaluation status

Final implementation checkpoint: `18f98d0`. Working directory:
`/home/san/Code/scientific-network`. Final candidate version and content hashes
are bound by [candidate-manifest.json](candidate-v3/candidate-manifest.json).

| Check | Actual outcome |
| --- | --- |
| Locked environment, analysis and report extras | Installed with `uv sync --locked --group dev --extra analysis --extra report`; exit 0 |
| Initial full suite | 524 passed, 7 skips; six skips caused by omitted optional report extra |
| Task 1 complete suite after restoring report extra | 533 passed, one existing skip; exit 0 |
| Initial Task 2 focused run | 18 failed / 75 passed: Pydantic URLs were not JSON serializable in decision hashes; fixed and rerun 93 passed |
| Intermediate full suites | 567 passed, then 570 passed; one existing skip in each |
| Multiple raw-account regression before fix | Failed as expected; source-compatible names and two accounts incorrectly resolved to two IDs |
| Final focused suite | `uv run pytest -q tests/test_mentions_v5.py tests/test_identity_audit_v5.py`: 49 passed; exit 0 |
| Final configured suite | `uv run pytest`: **579 passed, one existing skip**; exit 0 |
| Baseline census CLI | Exit 0; immutable hashes match, 341 cached objects verified, all retained source arrays equal, derived validation zero errors |
| Additive pipeline inventory CLI | Exit 0; historical guard fully explains missing supported positions, source-filtered citation inventory equals graph |
| Final candidate CLI and separate replay | Both exit 0; five data artifact hashes and paired-ranking JSON identical |
| Final offline validate CLI with `--require-size` | Exit 0; all size checks pass; zero structural errors; semantic accuracy unmeasured |
| Protected components | Canonical publication/citation/topic/taxonomy/source hashes equal; only enumerated paper reason changes allowed |
| Retained-position affiliations | Exact organization sets preserved on all 49,732 retained positions |
| Original snapshot preservation | 748 source/cache/v4 files hash-checked; zero changed files |
| Official retained inputs | Frozen roster hash and all retained fields/derived DOIs match original works; no roster reconstruction |
| Neo4j import/query integration | **Not run**; candidate remains files only and no import/query code changed |
| Collection, benchmarks, deployment, independent evaluation | **Not run**; no APIs, model downloads, production edits, new semantic labels or independent gold scores |

The existing skip is the empty pending-stage parameterization in `tests/test_cli.py`.
Intermediate failures are retained in ignored `reports/runs/WORK-2026-11-11-003/`
and summarized in the work log. An exploratory source probe initially failed on
null author IDs; the census uses null-safe ID handling. No partial source download
or replacement snapshot was created.

## Meaningful test coverage

[Resolver tests](../../tests/test_mentions_v5.py) cover equivalent Unicode,
diacritics, initials, hyphens and East Asian name order; homonyms on distinct IDs;
profile ORCID conflicts; direct raw crosswalks; missing ORCID and missing provider
ID; wrong alignment; repeated provider/canonical positions; one ambiguous position
beside verified coauthors; affiliation changes across papers; missing/malformed
and contradictory fields; ambiguous multiple ORCID accounts; and raw/profile
collision checks. Parameterized materialization cases assert exact resolved states,
researcher/authorship/coauthorship counts and absence of unsupported affiliations.
Other cases verify exact affiliation triples, distinct-author organization rules,
official team-size fractional denominators, deterministic artifacts, source hash
refusal, protected input bytes and output/symlink refusal. Both shadow-bug trigger
paths assert that a later conflicting ID remains withheld while a good ID survives.

[Audit tests](../../tests/test_identity_audit_v5.py) exercise overlapping reason
denominators, venue/year aggregation, tampered cache bytes, retained-source mismatch,
output alias/symlink/nesting protection, unsupported institution observations and
missing source-supported core citations. They are invented fixtures, not project
quality measurements.

## Reproducibility evidence and limits

[Reproducibility receipt](candidate-v3/reproducibility-receipt.json) records the
actual Python, Unicode, NetworkX, Pydantic, NumPy, pytest and PyYAML versions plus
`uv.lock` hash. Executed resolver/materializer/network code hashes match the current
files. The full input/config/code hashes and graph/ledger hashes are in the
candidate manifest; large data remain ignored. Two unused output directories
produce byte-identical graph, decisions, index, review queue and centrality scores.
Comparison manifests intentionally contain their actual output paths.

An additive [preservation supplement](candidate-v3/supplemental-preservation-v1.json)
also checks directory membership and confirms that the single recovered conflict
position occurs in the original v4 removal ledger. The committed replay receipt
is preserved exactly; the supplement does not silently revise it.

No independent identity reference set was available. Pairwise precision/recall/F1,
authorship precision/recall and true false-merge/split counts remain null. The
implementation is AI-assisted by Codex; there was no new semantic A/B review,
human annotation, independently verified ORCID ownership or new accuracy score.
The observed count/coverage changes cannot verify the course accuracy requirement.
