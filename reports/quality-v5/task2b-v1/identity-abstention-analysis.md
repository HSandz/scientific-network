# Identity abstention investigation — Task2B v1

The exact target frame is **170 provider IDs / 683 positions**, selected by the prior decision reason `author_id_incompatible_name_variants`. The old identity index contains 193 IDs with incompatible names; 23 have a higher-priority identity conflict and are outside this 170-ID reason frame. They are not silently recovered.

Every target ID has a cached evidence inventory and an explicit disposition. Public authoritative enrichment was prioritized by affected position count, then provider ID (deterministic tie break): public ORCID person records for the first 20 IDs; works lists for five declaring useful aliases; one Tsinghua academic profile as corroboration. No unrestricted crawling, paid APIs, author-profile bulk collection or affiliation inference occurred.

Classification is a reproducible observed pattern or explicit declaration, **not independently established ground truth about every person**. All 170 receive cached review; only 20 receive the new public ORCID review. No manual review is fabricated for the remaining records.

| Disposition | IDs | Positions | Action |
| --- | ---: | ---: | --- |
| Same full given-name letters with changed spacing/hyphen boundaries | 37 | 185 | Retain stable provider ID with aligned raw/official byline |
| Public ORCID explicitly declares all needed variants | 5 | 50 | Retain stable unconflicted provider ID; attach declaration evidence |
| Middle-name/initial variation without adequate declarations | 93 | 315 | Abstain |
| Different full names or spellings without sufficient crosswalk | 35 | 133 | Abstain |

The formatting rule preserves every ordered full given-name letter and the final surname token, excludes initials, and never substitutes letters, omits a middle name or connects different provider IDs. Existing Unicode/diacritic/order handling is unchanged. The rule checks all compatible-position names on the ID. Profile ORCID conflicts take priority. These are changed normalization decisions supported by a stable identifier and aligned bylines, not independently verified assignments.

The five declared-alias cases are construction evidence from public account owners, not independent test gold. The provider may ingest the same ORCID account. Public works lists were retrieved as an additional check but were sparse/empty for several accounts and do not independently establish every authorship. No missing ORCID-work entry is treated as disproof.

| Provider | Declared alias case | Restored positions |
| --- | --- | ---: |
| A5035664456 | Daniel D. Harabor / Daniel Harabor | 11 |
| A5044848288 | Anil Kumar Vullikanti / Anil Vullikanti | 11 |
| A5089442472 | Johannes Fichte / Johannes K. Fichte / Johannes Klaus Fichte | 11 |
| A5071538560 | John Dickerson / John P. Dickerson | 10 |
| A5020679327 | Munindar P. Singh / Munindar Singh | 7 |

Publication, coauthor and paper-specific institutional context is collected for all 683 positions in [provider-context.json](investigation/provider-context.json), including raw affiliation mappings, years and source locators. These fields prioritize investigation but never establish an identity by themselves. Official/raw/canonical names, raw/profile ORCIDs, provenance and alias declarations are in [provider-ledger.json](investigation/provider-ledger.json). The exact 170-row disposition table is [provider-classification.csv](investigation/provider-classification.csv).

High-impact unresolved examples include `A5017743551` (Bo An / Bohui An, 26 positions), `A5081837918` (Qi Yu / Yu Qiu, eight), and `A5100381753` (Ming Yang / Shuicheng Yan, seven). The observed names and current public ORCID name do not establish aliases, splits or which provider partition is correct. No false merge is asserted from the string difference alone, and no researcher split is guessed. Common names, transliteration and nicknames remain genuine ambiguity risks.

This restores 235 of the 683 positions; **448 positions / 128 provider IDs** remain in this name-variant abstention frame. Other global profile conflicts remain governed by the old shared collector. All 4,492 historical conflicting profiles remain unresolved globally; the one preexisting paper-raw-ORCID recovery is retained, without extrapolating its ownership to other papers.

## Missing-ID recovery

Among the original 6,285 matched positions missing provider IDs, 63 lie on works with preserved duplicate records. Twenty have a compatible ID at that position in an exact-DOI alternate; the final guarded recovery accepts **18**. All byline positions must align, existing nonmissing IDs must agree, IDs must be unique within the alternate, and full-source plus alternate ORCID/name conflicts must not contradict the candidate. A missing selected ID is never repaired by searching a same-name person. Two potentially usable positions fail the more complete checks. See the decision ledger and recovered-versus-v3 ledger for exact position-level outcomes.

Alternate work evidence receives a distinct locator-bound evidence ID even when it shares a raw batch hash with the selected work. Original evidence and affiliations remain intact. No new affiliations are inferred: newly accepted positions use only their original paper-specific institution mappings and copy guards. No unsupported cross-provider merge or new identity split occurred.
