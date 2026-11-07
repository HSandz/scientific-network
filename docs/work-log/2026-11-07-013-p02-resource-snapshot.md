# WORK-2026-11-07-013 — P02 local resource snapshot

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 20:56 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-012](2026-11-07-012-pregraph-source-followup.md) |
| Git state | main at 66e692d; extensive pre-existing uncommitted work preserved |

## Objective

Move P02 forward independently of the blocked P01 source captures by measuring
current local storage and memory use without collecting papers, querying providers,
starting enrichment, or changing frozen assignments. Keep these figures scoped to
the current workspace snapshot; they cannot establish full-population feasibility.

## Changes and findings

- Task opened after confirming the Sites Git host and the current CIKM/ACM hosts
  still fail DNS resolution. Current workspace and pregraph planning instructions
  reviewed.
- At 20:59 +07:00 the workspace filesystem had 841,169,092,608 bytes (783.40 GiB)
  available. Host `free -b` showed 4,248,862,720 bytes (3.96 GiB) available memory
  and 3,782,856,704 bytes (3.52 GiB) swap used. The visible `init.scope` cgroup
  reports `memory.max=max` and `cpu.max=max 100000`; its current memory usage was
  7,045,214,208 bytes (6.56 GiB).
- Apparent sizes from `du -sb` were 2,129,380,195 bytes for `data/manifests`,
  1,402,701,631 for `data/raw`, 97,963,131 for `data/interim`, 14,519,586 for
  `data/processed`, and 270,100,679 for `reports/runs`, totaling 3,914,665,222
  bytes (3.65 GiB). These files span historical and diagnostic artifacts and are
  not a full-corpus forecast.
- Docker storage could not be measured: `docker system df` exited 1 because access
  to `/var/run/docker.sock` was denied. The exact sanitized snapshot is in the
  ignored `reports/runs/WORK-2026-11-07-013/resource-snapshot.json` artifact.
- P02 remains no-go. No provider requests, PDFs, enrichment, new samples or graph
  operations were made; this snapshot does not size future backup/database volumes
  or reviewer time.
- The user reports one reviewer, with no exact hours known. A second independent
  reviewer is unconfirmed; the required two-review audit capacity therefore cannot
  be budgeted from the available information.
- Refreshed the local Report snapshot with the reviewer-capacity status and P02
  no-go. It is not published because the Site source helper's DNS blocker remains.
- A metadata-only scan of the 562 local five-year source-cache request descriptors
  found no URL for `cikm2025.org`, `2024.acmmm.org`, or `git.chatgpt-team.site`.
  No raw source object was opened; P01 still lacks locally captured sources for
  these routes.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `df -B1 --output=size,used,avail,pcent,target . /tmp` | passed (0); 783.40 GiB available on workspace mount | `reports/runs/WORK-2026-11-07-013/resource-snapshot.json` |
| `free -b` and cgroup-v2 read | passed (0); host available memory 3.96 GiB; visible `init.scope` memory/CPU quota unbounded | Same resource snapshot |
| `du -sb data/manifests data/raw data/interim data/processed reports/runs` | passed (0); selected existing data/run footprint 3.65 GiB apparent size | Same resource snapshot |
| `docker system df` | failed (1); permission denied on Docker socket, storage volumes unmeasured | Failure saved in resource snapshot |
| Individual `getent ahosts` probes for `git.chatgpt-team.site`, `cikm2025.org`, and `2024.acmmm.org` | all failed (2); source-network condition unchanged | P01 remains pending hash-bound local capture |
| Source-cache request metadata scan | passed; 562 descriptors, none reference the three target hosts | No raw source body opened |
| User reviewer-capacity response | one reviewer reported; exact hours unknown; second reviewer unconfirmed | Required two-review budget remains unestablished |
| `uv run pytest` / offline CLI | not run; documentation and resource-measurement iteration only | No code path changed |

## Decisions

None. Existing no-go and scope boundaries remain in force.

## Open issues and limitations

P01 remains incomplete and P02 still lacks the canonical work frame, prospective
P03 design, provider budgets, cold-processing measurements and a second reviewer
with confirmed hours. One reviewer is reported, but their time availability is
unknown. A local host snapshot is transient and cannot stand in for those items.

## Next step

After P01 sources and a prospective P03 batch are fixed, secure a second independent
reviewer and both reviewers' available hours, then recheck Docker/database storage,
provider quota and cold throughput against that exact batch.

## Corrections

None.
