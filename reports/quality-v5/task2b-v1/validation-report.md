# Validation and reproducibility — Task2B v1

Final candidate: `release-identity-v5-503aafe10a31`, graph SHA256
`85ff09d0a5e6a42160a3c98fad3f63941a2b412213490f4c7f744ed5e2ba4d4e`.
Code checkpoint `eab4dce`; machine outcomes and transitive code/config/input hashes
are in [validation-receipt.json](validation-receipt.json). Exact CLI reproduction
and ignored source restoration requirements are in [README.md](README.md).

| Executed check | Outcome |
| --- | --- |
| `uv sync --locked --group dev --extra analysis` | Exit0; report extra removed by sync, explaining baseline skips |
| Initial `uv run pytest -q` | 573 passed / 7 skips, exit0; six report-extra skips, one existing empty CLI parameter set |
| `uv sync --locked --group dev --extra analysis --extra report` | Exit0; optional report environment restored; no dependency or lock changes |
| `uv run pytest -q tests/test_identity_recovery_v5.py tests/test_mentions_v5.py tests/test_release_acquisition.py` | Final 115 passed, exit0 |
| `uv run pytest -q` after final code/test changes | 603 passed / one existing empty-parameter skip, exit0 |
| Final candidate build and separate full replay | Exit0 each; all five data files byte-identical and paired rankings byte-identical |
| `research-network validate ... --require-size` | Exit0; zero structural errors, all relation/size checks pass; derived support and weights checked |
| Original source verification during both builds | All 13,606 matched retained work projections equal 341 hash-verified cached objects |
| Public evidence verification/cache replay | 40 successful original public requests, all 40 raw objects hash-verified; later source replay used cache |
| Original-file preservation and membership | All 779 recorded original files unchanged; original protected directory file membership identical |
| Frozen evaluation packets | Every recorded packet/sample/form hash still equals the initial freeze |
| Three-way comparison/scoring | All checkpoints evaluated on the same frozen frames; semantic scores correctly unavailable with zero independent references |
| Final transitive execution-code hashes | Equal current code and candidate manifest; no inference/model retraining |
| Neo4j integration | Not run: no load/query/service code changes and no DB access needed; no DBMS validation claimed |
| Push/deploy/application checks | Not run; no production/application changes made |

The complete suite includes existing same-name, provider split/overmerge, conflicting
ORCID, raw ORCID, byline-order, affiliation mapping, repeat support and derived-edge
cases. New regressions cover full-letter spacing boundaries and false positives,
public alias declaration provenance/hash/account binding, contradictory external
identifiers, absent IDs on duplicate works, wrong DOI/order/provider partitions,
ORCID conflicts in alternates, sampling replay/overwrite refusal, paired scoring,
and same-batch alternate evidence preservation. Synthetic tests are not identity
benchmark results. Structural graph validation is not semantic accuracy.

Original graph component protection checks prove unchanged paper/venue/topic
metadata (apart from explicitly enumerated identity-only unresolved reasons),
citation/topic/publication/taxonomy claims and original nonderived evidence.
Added identity evidence is enumerated, rather than deleting original records to
make hashes agree. Retained-position affiliation organization sets are exactly
preserved against both v4 and v3. No Task3 mappings or topic predictions changed.

Data outputs (`graph.json`, `identity-decisions.jsonl`, `identity-index.json`,
`review-queue.jsonl`, `centrality-scores.json`) and ranking reports reproduce
byte-for-byte. Final comparison JSON values/order reproduce after normalizing
recorded output paths. Location-dependent manifests include real output paths and
are not claimed byte-identical. Every final input/code hash matches the receipt.

## Failures and preserved intermediate results

An initial ignored investigation script named `inspect.py` shadowed Python's
standard library and failed before producing its snapshot; it was renamed and
rerun successfully. A newly added test fixture initially lacked its output
directory (114 tests passed / one failed); directory creation fixed the fixture,
then all 115 focused tests and the full suite passed.

The first candidate (`identity-candidate-v5.4`) replayed all data and rankings
exactly, but comparison reason-count dictionaries serialized in different orders.
Values were identical. Final method v5.5 sorts those dictionaries and adds explicit
transitive code hashes; no acceptance rule/count changed. The original Task2B
candidate/reports and local replay remain preserved, with superseding notes.
The initial investigation-summary category map also had arbitrary key order;
its values are preserved and replay now sorts that map. Detailed ledgers and
certificates are unchanged; key-order changes are not scientific data changes.

No independent identity reference labels, human annotation, independently validated
false-merge/split counts or verified precision/recall/F1 were obtained. The actual
scorer returns null metrics and intervals. Historical AI edge audits were not
rescored as identity gold. Graph size and additional accepted positions establish
coverage changes only. The unchanged-work identity candidate does not demonstrate
that it meets semantic accuracy or end-to-end affiliation targets.
