# P02 feasibility checkpoint — no-go for broader enrichment

Checked **7 November 2026 (Asia/Bangkok, UTC+07:00)** for
[WORK-2026-11-06-009](../docs/work-log/2026-11-06-009-pregraph-source-closure.md).
This is a bounded feasibility decision from current evidence, not a forecast that
the complete project can meet its release gates by the deadline.

## Decision

**Do not start broader enrichment.** Keep the next metadata, ORCID, PDF, model, and
annotation budget at zero until P01 source closure, P03 prospective sampling, and
actual resource/reviewer feasibility are demonstrated. No paid spend is authorized.
This iteration made no enrichment requests and collected no papers or PDFs.

## Current evidence and limits

- The v6 roster has 88,608 observations, 85,850 included and 2,758 excluded. It
  records 89 eligible editions and 81 gaps. The 85,850 observations are not a
  deduplicated canonical-work count. One hundred sixty edition observations are
  inherited from the v2 baseline; only the ten AAAI/ICAPS target editions were
  refreshed by the OJS workflow.
- Existing D023–D025 work is a 68-paper development diagnostic, not a
  representative full-population yield study. Historical D024 recorded 283,508,927
  PDF bytes, 66 parsed headers and two retained parser failures. Historical D025
  recorded 10 publicly corroborated researchers, 11 authorship supports, 12
  affiliation triples, and 339 current queue rows. Those measurements do not
  estimate five-year identity, affiliation, topic, or citation yield.
- The 2,000 core researcher target remains a separate feasibility question. The
  current ten-person development evidence does not support extrapolating that target
  or calculating a requests-per-researcher budget.
- No current OpenAlex/ORCID quota, provider unit weight, cold parser throughput,
  free disk/storage allowance, or service health was checked in this iteration.
  Existing 10k/50k/100k scenarios in
  [`five-year-planning-estimates-2026-11-06.json`](five-year-planning-estimates-2026-11-06.json)
  are hypothetical sensitivity cases, not a size forecast or measured budget.
- The user reports **one reviewer**, with no exact hours known; a second independent
  reviewer is unconfirmed. The two-review audit requirement therefore has no
  executable human-capacity budget. Under the existing 3–6 minutes per edge per
  reviewer assumption, 600 global audit edges require 60–120 person-hours across
  two reviewers. Global plus per-type review could require 60–320 person-hours,
  with a further 5–33.33 hours for the stated adjudication assumption. An
  illustrative 50-paper component set would require 33.33–66.67 person-hours; it
  is not an approved sample.

## P02 local workspace snapshot — WORK-013, 7 November 2026

At **20:59 +07:00**, the workspace filesystem reported **841,169,092,608 bytes
(783.40 GiB) available**. The visible `init.scope` cgroup showed no memory or CPU
quota (`memory.max=max`, `cpu.max=max 100000`); host `free -b` reported
4,248,862,720 bytes (3.96 GiB) available memory and 3,782,856,704 bytes (3.52
GiB) swap in use. These are transient environment observations, not guaranteed
resources for later services or jobs.

The apparent sizes of `data/manifests`, `data/raw`, `data/interim`,
`data/processed`, and `reports/runs` sum to **3,914,665,222 bytes (3.65 GiB)**.
This combines historical and diagnostic artifacts; it is not a per-paper
production estimate. `docker system df` could not inspect graph/database storage
because access to `/var/run/docker.sock` was denied. The exact sanitized snapshot
is kept in the ignored [WORK-013 run artifact](runs/WORK-2026-11-07-013/resource-snapshot.json).

This snapshot shows substantial free workspace disk at measurement time but does
not size backups, isolated Neo4j volumes, the deduplicated full corpus, provider
quotas, cold processing, or reviewer time. **P02 remains no-go for broader
enrichment.** Do not use these machine figures to relax any gate or authorize a
paper batch.

## Stop rules

1. Do not issue enrichment, PDF, or model requests while 81 edition gaps remain and
   the complete intended population is unknown.
2. Do not set a paper batch size or draw a supplemental sample before P03 freezes
   the version-aware population, all old test memberships, new test reservations,
   inclusion probabilities, nonresponse handling, and reviewer budget.
3. Recheck live provider quotas, request credits, storage, and cold processing only
   for the prospectively bounded batch. Keep paid spend at $0.
4. If the measured batch cannot project a credible route to unchanged size,
   coverage, and quality gates within available free resources and real reviewer
   hours, stop and report no-go. Do not turn existing diagnostic yields into a
   production promise.

## Next bounded task

Continue P01 source-route and edition verification. Then finish P02 using the
deduplicated frame and actual free-resource/reviewer measurements, before P03
sampling or any new enrichment. Keep all prior assignments and the v2-bound
diagnostic/pregraph artifacts unchanged.
