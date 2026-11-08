# WORK-2026-11-08-029 — Release Phase 5 topic test freeze

| Field | Value |
| --- | --- |
| Status | completed (Phase 5 partial) |
| Recorded | 2026-11-08 12:00 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 11:52–12:00 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-2026-11-08-028](2026-11-08-028-release-phase-3-verification.md) |
| Git state | `main` at `870bc0c`; Phase 5 freeze changes ready for local commit |

## Objective

Complete the Neo4j-independent first step of Phase 5 while Phase 4 is blocked by missing
Docker Desktop WSL integration. Freeze the D040 topic test IDs and version/leakage holds
before inspecting classifier predictions or tuning thresholds.

## Changes and findings

- Added `research-network freeze-topic-test`, implemented in
  [topic_test.py](../../src/scientific_network/nlp/topic_test.py). It selects by
  SHA-256 rank, refuses output overwrite, binds all source files by hash, preserves the
  existing split assignments, rejects groups intersecting development, and carries all
  candidate version IDs into `heldout_paper_ids`.
- Froze [topic-test.jsonl](../../data/manifests/release-v1/topic-test.jsonl): 30 of the
  80 existing in-scope IJCAI test papers plus 20 newly reserved AAAI papers, seed
  `20261108`; 50 unique paper IDs and 50 held-out paper/version IDs. The file contains
  IDs and sampling metadata only—no title, abstract, prediction or labels.
- Input hashes: roster `84ff8ca78073e5d5e0d94f909aac63d18d71435cbd60f30630b7c3090b3c1cbe`,
  frozen membership `fdaa5e742c7c2e4a96c2d1d70df48103f758ec82fbbe01f8005adb4598aa674f`,
  leakage ledger `5489c0afc9d3a3699ce161826dbd427f44174293c8cc306b93333c4e2b72908b`.
  Manifest sha256: `90d01d6483d9fe84eec055e78cf17b2a8e4f26440250488fc548c510c89158d8`.
- Added [topics-release-v1.yaml](../../configs/topics-release-v1.yaml) as a separate
  development copy (`taxonomy-release-v1`, `development_before_freeze`); model and
  thresholds remain unset. The historical taxonomy config is unchanged.
- Phase 4 remains incomplete: Docker Desktop reports its CLI is unavailable in this WSL
  2 distro; the release database has not been started.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run research-network freeze-topic-test --seed 20261108 --output data/manifests/release-v1/topic-test.jsonl` | passed, exit 0; 30 IJCAI + 20 AAAI | manifest sha256 above |
| `uv run pytest -q -p no:cacheprovider tests/test_topic_test_freeze.py` | passed, exit 0; 2 passed | deterministic repeat, version holdout, dev-overlap rejection and no-overwrite tests |
| `uv run pytest -q -p no:cacheprovider` | passed, exit 0; 347 passed, 1 skipped | skip is the existing empty parameter set in `tests/test_cli.py` |
| Manifest audit | passed | 50 unique IDs, exact venue/sample counts, all IDs have seed/source/hashes; no content or prediction fields |
| `git check-ignore` for new manifest/config | not ignored | artifacts are suitable for Git tracking |

## Decisions

Use seed `20261108` and deterministic SHA-256 rank ordering. Keep the test taxonomy in
development status until the embedding model and thresholds are frozen on development
data only. No test title, abstract, prediction or reviewer label was inspected.

## Open issues and limitations

This checkpoint freezes only the topic test frame. No embedding model, threshold tuning,
graph v2, label sheet or human topic labels exist yet. Phase 5 cannot close until Phase 4
Neo4j integration is restored and graph v2 is loaded.

## Next step

Continue Phase 5 only on non-test data: pin the CPU embedding model/revision, calibrate
thresholds on development papers, then build and validate graph v2. Return to Phase 4 for
release database load and replay when Docker Desktop WSL integration is available.

## Corrections

None.
