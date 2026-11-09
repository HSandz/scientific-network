# Local release and external delivery checklist

Follow D040 and the agent evaluation workflow. This checklist does not authorize
external delivery and is not a claim that the lecturer accepts AI-only evaluation.

## Local evidence

- Content freeze: `reports/release-v2/freeze-v3.json` (unchanged graph/classifier).
- Evaluator freeze: `reports/release-v3/evaluation-freeze-v1.json`.
- Blind-topic completion: `reports/release-v3/topic-completion-freeze-v1.json`.
- Completed exports/source ledgers: `reports/release-v3/completed/`.
- Scoring receipt/results/limitations: `reports/release-v3/`.
- Academic report: `reports/final-report/report.md`.
- Reproduction/render commands: [reproduce-agent-evaluation.md](reproduce-agent-evaluation.md).
- Final local package receipt and actual checks: linked from the current status
  and final work entry. An ignored smoke render is not the final package.

A failed numeric audit threshold remains a reported finding. It does not authorize
retuning, resampling or replacing judgments. AI-assessed scores do not establish
verified course accuracy, human validation or evaluator independence.

## Facts still needed from real records

1. Real student names/IDs and actual contributions for `docs/team.md` and report
   section 1. Do not infer membership or credit from Git accounts or A/B channels.
2. The lecturer's required access to the repository/demo and course-specific
   AI-use disclosure rules. Existing agent disclosures remain explicit.

The local report/package can be prepared while these remain pending. It remains
a draft for submission until those facts are supplied and reflected in a new
versioned render/package. Preserve the previous package receipt.

## Separately authorized delivery

When the user explicitly authorizes the concrete delivery:

1. Review the final local commits, audit failures/limitations, package hashes and
   pending facts. Confirm the actual remote refs and repository access choice.
2. Push only the agreed commits; create/push an agreed release tag. Do not claim
   a release URL exists before it is created and verified.
3. Attach the ignored PDF/local permitted bundle to the authorized release or
   course submission. Keep raw downloads, full graph caches, credentials, models
   and database volumes outside Git and the submission bundle.
4. If requested, perform the single final update to the existing public Site under
   `docs/sites-workflow.md`; preserve project ID/URL/audience/Plan and native Report
   controls. No intermediate publications or iframe embedding. Record the actual
   publication receipt under `docs/reference/`.
5. Give the lecturer the specifically authorized access/invitation and submit
   using the real course destination. Verify receipt rather than infer success.

No push, tag, Site publication, invitation or submission is performed by local
scoring, rendering or packaging.
