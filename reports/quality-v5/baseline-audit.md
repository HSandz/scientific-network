# V5 baseline quality audit — Task 1 checkpoint

Census of unchanged frozen v4 and existing cached inputs at HEAD `acd57c4`.
This is not semantic accuracy evaluation. [Machine results](baseline-audit.json)
contain all ten venue/year strata and input hashes; [issues](issue-inventory.csv)
prioritize findings. No collection, database access or graph mutation.

## Verified baseline

Graph hash matches freeze: `release-d3c788c3114a`,47,875 nodes,225,731 edges,
32,189 resolved researchers,110,026 factual edges.13,606/13,617 work rows matched;
11 review (9 duplicate DOI,2 count disagreement). Official positions65,507;
matched65,469;accepted50,437;withheld15,032;affiliated48,259/65,469=73.7127%.
All13,606 retained authorship/reference arrays equal their original cached objects
at exact work locators;341 content hashes verified. This is byte equality,not
provider correctness. Structural/derived validation:zero errors;missing edge
evidence IDs:zero. No unresolved people are domain nodes;many mentions unresolved.

## Pipeline inspection

| Stage | Inputs and acceptance | Withholding/missingness | Risks,consequences and provenance |
| --- | --- | --- | --- |
| Proceedings | Official frozen v10 byline,URL,year,main track;hash-pinned roster | Enrichment failure keeps paper/venue | Parser/source limits remain;no roster/rights/source-route audits rerun. URL,hash,time,locator retained. |
| Work matching | Derived DOI,title similarity≥.9,count agreement;264 duplicates choose unique official landing page,66 differ in author IDs |11 review;two accepted titles nonexact;one year disagreement | Seven singleton responses carry different DOIs. Batch assignment checks DOI;singleton fallback does not. Possible proceedings/journal version confusion propagates all downstream claims. |
| OpenAlex | Immutable responses,raw names,author objects,institutions,raw strings,abstract,references |6,285 positions lack author ID;2,182 lack institutions;22 paper raw ORCIDs | Author-object ORCIDs are not paper-specific.341 original objects hash-checked;no profile/ORCID-owner/PDF/header independent validation. |
| Researchers | v1.1 compatible positional raw OR canonical name and provider ID;v4 checksum-valid singular+observed union |8,727 source positions on4,492 conflicting IDs;8,722 v3-accepted removed | Global withholding loses support without proving false merges existed. Five exact canonical-only matches expose fallback risk. Current v1.2 state bug is separate from v4 history. |
| Affiliations | Author-specific institutions,prefer exact string→institution mapping;triples before aggregation | Copy guard;unknown institution IDs discarded |74,485 assignments,all have mapped strings/ROR;8,369 multi-institution positions;fallback mapping=0.146 copy-guard patterns/560 positions on surviving authors only,not exact historical exclusion census. Institution changes may be legitimate mobility. |
| Base graph | Semantic keys,resolved authors,roster-backed venue,in-core references |199 authorless papers;unresolved mentions excluded from nodes | Work-level evidence is not identity proof. Stable IDs,source/method/graph versions retained. Thresholds pass structural gates only. |
| Derivation | R7–R10 from accepted base support,distinct papers,canonical pairs,fractional weights | Unresolved positions remain in official team denominator;sole dual-affiliated author creates no R8 | Identity errors propagate collaboration,organization support,topic profiles and centrality. Recomputed validation passes;source meaning unverified. |
| Evaluation | Frozen v4 uniform AI edge sample193/200=96.5%;Wilson92.95–98.29% | No independent identity labels or new untouched topic test | Intervals exclude judge/source error. Historical errors are development diagnostics only;no v5 accuracy claim. |

## Root causes and overlapping populations

Primary absence reasons reconcile exactly to15,032:8,722 ORCID conflicts,
6,283 missing IDs,18 compatible positions rejected by repeated-ID whole-paper
guard,2 compatible positions rejected by multiple-name guard,and7 name mismatches.
Missing IDs total6,285 because categories overlap. Three papers repeat provider
IDs (six repeated positions);two have multiple incompatible names.

All4,492 conflicting IDs repeat one identical observed-array set across their
works;none changes singular ORCID across these cached works. Only one has paper
raw ORCID;none has multiple distinct paper raw ORCIDs. Compatible with profile
aggregation error,but cannot establish how many represent distinct real people.
Never split by array entries.3,461 normalized-name groups have multiple provider
IDs and535 ORCID groups share provider IDs:inspection leads,not false-split counts.
JSON records varying-name/affiliation/institution counts and influential withheld
source IDs. Their source-neighbor counts are not accepted graph degree.

## Confirmed state bug and historical impact

Builder v1.2 reuses `withheld` for its dictionary and whole-paper reason string.
After either trigger(two name mismatches or repeated usable ID),membership becomes
a substring test:ordinary `A…` IDs escape withholding. Synthetic reproduction
accepted conflicting A3 on paper2 after paper1 rejection. First source trigger:
`paper:aaai:2021:16134`;8,696 later name-compatible conflict positions exposed to
lost lookup. This is an exposure count,not an asserted complete rerun edge count.

`git show 870bc0c:src/scientific_network/resolve/release.py` proves v1.1 checks a
separate `conflicted` set. Frozen v4 filters that older graph using the collector;
it never calls the buggy builder. Freeze declares base v1.1;v4 hash verified.
No evidence this new bug corrupted v4;unrecorded runs cannot be ruled out.

## Topics,citations and network effects

Frozen topics:11,575/13,617 labeled,14,222 assignments. Historical AI-reference
embedding micro-F1=.4667 is not independent truth.378,360 reference occurrences
have no within-work duplicate IDs;1,048 matched works lack references;7,308 core
citations cannot establish complete reference recall. Seven DOI-disagreement works
need review. This phase preserves topic/citation claims and implements no improvement.

V4 researcher network:2,936 components,414 isolates,largest20,776/32,189.
Existing historical v3 comparison (not rerun v3 analysis):2,278 components,
193 isolates,largest26,990/36,680 and31,560 more coauthorship pairs.
Withholding changes the network materially;more edges do not prove accuracy.

## Remediation order / Task 1 exit

1. Fix state shadowing;regress both whole-paper triggers and subsequent conflicts.
2. Implement deterministic mention ledger with resolved/ambiguous/unresolved states.
3. Require matching DOI/count for candidate identity claims;separately account for
source-gate losses on mismatched works without rewriting frozen source decisions.
4. Recover unique raw-name position anchors and direct paper raw ORCID only with
corroborating names. Never select observed-array ORCID or merge by name.
5. Preserve remaining mentions;recompute R7–R10;compare support and networks.
6. Leave semantic P/R/F1 and false merge/split counts null without independent
references. Task3 must preserve exact affiliation triples and audit abstentions.

Task 1 established before Task 2 implementation. Reproduction: [README](README.md).
