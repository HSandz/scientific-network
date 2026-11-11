# Independent identity annotation guide

The two team members act as A and B, with their actual names or stable reviewer IDs.
Both review the same 511 frozen cases independently. Production candidate IDs,
construction profiles, recovered mechanisms and the other person's answers are
withheld in the initial workspace. Read the paper before deciding who the person is.
Do not read candidate comparison/investigation reports until your blind export is
frozen. Additional source links are leads, not suggested labels.

## Start the local workspace

Use the exact commands in [README.md](README.md). Serve the assigned **role directory**
on its own localhost port. Give reviewer A only `workspace/A`, and B only
`workspace/B`. Use different browser profiles or computers; local storage is draft
storage, not authentication or an access-control boundary. Keep exported review
files in ignored `data/annotations/` or `reports/runs/`, not in public source control.

Choose assignment, pair or diagnostic in the category filter. The queue shows stable
case IDs. A paper panel contains title, venue/year, DOI, official links, complete
byline and the selected position in green. Pair cases have two paper panels.
Completed/remaining counts and cases needing evidence update from saved judgments.

## Labels

For an assignment:

- **Verified identity**: independent paper-specific evidence establishes the person.
  Enter a persistent person URL or stable reference identity anchor. Do not enter a
  candidate/provider ID just because it appears in construction metadata.
- **Insufficient evidence**: ownership or crosswalk cannot be determined. This is a
  completed unknown judgment, not an incorrect identity and not an affirmative rejection.
- **Invalid identity claim / unresolvable**: affirmative authoritative evidence shows
  that no valid person assignment exists at this official position (for example an
  officially corrected bogus byline). This should be rare. A possibly wrong provider
  ID is not enough: if the real author can be established, label that identity instead.

For a pair:

- **Same person**: independently anchored paper ownership links both positions to one person.
- **Different people**: positive evidence establishes distinct people, not just two
  different ORCID accounts or affiliations.
- **Cannot determine**: one or both paper ownerships remain uncertain.

A name, current affiliation, topic, coauthor overlap, OpenAlex ID or construction
ORCID alias alone is insufficient. A paper PDF may establish byline/email context
without proving canonical person ownership. A duplicate OpenAlex record is provider
construction evidence. Absence from an author's page does not prove non-authorship.

## Evidence and preservation

For every source record enter URL, retrieval date/time with timezone, SHA-256 of
retrieved bytes, exact locator (page/author marker or link), minimal excerpt, source
owner, provenance/upstream data and an independence explanation. The optional file
input computes the source hash locally without uploading anything. Add as many
sources as needed before saving. Keep full cached material local; do not redistribute
PDFs or private annotations. Enter confidence and reasoning, including contradictions.
`independent` means independence of the specific claim from construction evidence,
not merely a different domain. Mark shared upstream or unknown honestly.

Save each judgment. Export at each work break. Exported submissions have schema
`identity-review-v2`, frozen study SHA-256, reviewer identity, stable case IDs,
evidence and date. Import accepts only the same role/freeze; conflicting existing
judgments require a fresh profile to restore another version. CLI validation is the
authoritative strict check; keep every submitted version and its hash. Never alter
the original blank reviewer assignments or the frozen samples.

## Adjudication and identity crosswalks

After **both** reviewers have frozen exports, validate them with the CLI, then load
A and B files into the separate adjudication workspace. It shows original labels,
notes and source records only where both reviews exist. The disagreements filter
shows disputed cases; matching labels still require documented consensus. The two
teammates may jointly record consensus or adjudication under their real identities;
a third independent reviewer is not required or invented. Unknown disagreements
remain `unresolved` and keep label `unknown`.

After the initial independent annotations, inspect all three candidates to map each
verified reference person to its legitimate canonical ID(s). Record independent
crosswalk evidence and rationale. If absent from all three, save an explicitly
complete empty crosswalk: the person still belongs in the recall denominator.
If the mapping itself cannot be justified, preserve uncertainty. A candidate ID
containing an OpenAlex ID does not prove that its whole publication cluster belongs
to the reference person. Review source overlap and conflicting paper assignments.
The compiler binds adjudications to SHA-256 of **both original export bytes** and
preserves their labels. Do not pretty-print or edit an export after adjudication.

Export `adjudications.jsonl`; run the compiler and analysis commands in README.
Human-reviewed references and AI assessments are written to separate files. Actual
AI diagnostic judgments require actual model/run metadata through the schemas;
the human UI cannot turn an AI judgment into a human review. No labels have been
submitted in Task2C.

## Worked examples (invented, not project measurements)

1. An author's maintained bibliography links the exact paper DOI and a publisher
   byline contains the same personal identifier. Both reviewers establish reference
   `person:X`; later crosswalk evidence supports candidate `researcher:X`. A candidate
   accepting `researcher:Y` gets FP and FN. A candidate abstaining gets FN.
2. The author is independently established but absent from every candidate. A
   completed empty crosswalk preserves their identity and all candidate recalls
   count an omission. Uncertainty about which candidate ID is correct is instead unknown.
3. Two papers have the same name and provider ID but no ownership evidence. Pair
   label is unknown; do not call them the same person. Two independently anchored
   distinct authors incorrectly joined by a candidate create a false merge.
4. Two positions belong to the same independently anchored person. If the candidate
   uses different IDs, or accepts only one endpoint, the pair is a false split in
   this blocking frame. Outside-frame pairs are not estimated.
5. An ORCID work list used to accept an alias cannot be reused as independent gold.
   An official PDF without persistent identifiers may verify the byline while
   leaving ownership unresolved. Record that useful evidence and preserve unknown.
