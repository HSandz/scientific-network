# WORK-2026-11-24-002 — Runtime checkpoint

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-24 11:06 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-24 |
| Contributor | Codex |
| Related task | [WORK-2026-11-24-001](2026-11-24-001-local-llm-server.md) |
| Git state | `main` at base `3489d5b` before checkpoint |

## Objective

Commit and push the local runtime setup and its documentation. Keep changes in
`docs/prompts/` local at the user's request.

## Changes and findings

- The new docs index link depends on the excluded prompt, so both stay local.
- The named model preset contains only runtime settings and public model metadata.

## Verification

| Command/check | Outcome |
| --- | --- |
| `uv run pytest` | Exit 0, 650 passed and 1 skipped |
| `docker compose -f ops/llm/compose.yaml --env-file ops/llm/qwen3.5-4b-q4km.env config --quiet` | Exit 0 |
| Python `ast.parse` on both runtime smoke scripts | Exit 0 |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json` | Exit 0, structural check passed |
| `git diff --cached --check` | Exit 0 |

## Decisions

None.

## Open issues and limitations

Model inference was not rerun. Historical checks are recorded in WORK-2026-11-24-001.

## Next step

Freeze the enrichment splits and benchmark questions, then implement the LLM client.

## Corrections

None.
