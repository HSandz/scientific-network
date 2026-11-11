# Researcher identity evidence analysis

See [baseline](baseline-audit.md) for census and historical policy. Observed ORCID
arrays live inside `authorships[].author`,not the author-position field. Every
conflicting array is constant across cached works. They establish neither which
ORCID owns a paper nor whether the provider merged people. Paper `raw_orcid`
exists on22/65,469 positions,one of8,727 conflict positions.

The one conflict/raw case: `paper:ijcai:2024:208`,position2,provider `A5113306687`.
Source SHA256 `f65ae2c1c9c75b44ce50d395549157cd4218c57d03fdd1d387f96a57f82da941`,
`results[41].authorships[1].raw_orcid`. Official name:Wim Van den Broeck;
raw name has expanded middle names;canonical display matches official.
Raw ORCID `0000-0002-5305-7348` differs from selected author-object ORCID
`0000-0001-6683-5658`;both occur in observed array. No v4 researcher node has the
raw ORCID. This potentially anchors one position,not all papers on this provider
ID. Candidate must retain contradiction and isolate person ID from provider ID.
ORCID ownership has not been independently verified.

6,285 positions lack provider ID;names,affiliations and coauthors cannot supply
canonical identity. Three duplicate-ID papers require blocking repeated positions
while inspecting unrelated unique anchors. Two papers with multiple name
mismatches require retaining mismatch review,not guessing byline permutations.
An exact raw-name anchor can support an unaffected position only when unique
across both full bylines. Alternate spellings beyond normalization require direct
identifier evidence;Unicode/initial handling alone cannot merge people.

Shared names/aggregate ORCIDs and changed institution sets are leads,not proven
errors. Existing evidence cannot quantify true false merges,false splits,pairwise
P/R/F1 or authorship recall. Historical AI-audit cases are exposed diagnostics;
none becomes independent gold for this candidate.
