# Five-year official source-route triage

Checked **8 November 2026 (Asia/Bangkok, UTC+07:00)** as bounded P01 route
research. This page records route leads and source-closure outcomes; eligible
records are added only through the cited immutable v7–v10 recovery outputs. The
triage itself creates no separate roster, paper PDFs, splits, or enrichment;
official program PDFs and the ICDM 2025 HTML source pages were captured as source
evidence and remain ignored locally.

## D037 ICDM 2025 official accepted-list audit (WORK-020)

Fresh direct captures of the [official accepted-paper page](https://www3.cs.stonybrook.edu/~icdm2025/acceptedpapers.html),
[main CFP](https://www3.cs.stonybrook.edu/~icdm2025/cfp.html),
[BlueSky call](https://www3.cs.stonybrook.edu/~icdm2025/cfbtp.html), and
[program](https://www3.cs.stonybrook.edu/~icdm2025/program.html) returned HTTP
200 on 8 November 2026. Response status, dates, ETags, byte counts, body hashes,
and response-header hashes are recorded in [source corrections v10](../data/manifests/five-year-source-corrections-v10.json).
The accepted-page bytes match the earlier WORK-010 local capture; that earlier
file had no retained HTTP response metadata, now corrected by this recapture.

The accepted page has two complete sequential sections: **105 Regular** and
**70 Short** entries, **175 unique IDs** overall. Its heading conflicts with the
main CFP's statement that there is no separate short-paper submission track. The
CFP says accepted main-conference papers go to IEEE Computer Society proceedings,
with author registration and presentation required for proceedings inclusion.
The separate BlueSky call says its accepted papers appear in workshop
proceedings. The official schedule has **97 distinct DM IDs**, 95 also in the
accepted page; normalized exact-title comparison matches 94 accepted titles.
This does not reconcile every accepted record to final proceedings membership.

A candidate [IEEE Xplore contents route](https://ieeexplore.ieee.org/xpl/conhome/11391637/proceeding)
returned HTTP 418 to a direct HEAD request; no bypass was attempted. Individual
search-rendered publisher records do not supply a complete roster. The captured
conference pages state no metadata license or bulk-reuse permission; their
generic footer copyright link does not establish content ownership or permitted
reuse. Therefore ICDM 2025 remains **unresolved** in roster v10 and no roster v11
was created. Keep raw pages ignored and publish aggregate counts and official
links only. Do not infer accepted records that were included in proceedings.
See [D037](decisions.md#d037--icdm-2025-accepted-list-audit-2026-11-08),
[source corrections v10](../data/manifests/five-year-source-corrections-v10.json),
and [WORK-020](work-log/2026-11-07-020-icdm-2025-offline-source-audit.md).

## D038 ACM Multimedia 2024 browser-source follow-up (WORK-021)

The connected browser loaded the official [regular-paper call](https://2024.acmmm.org/regular-papers)
and [conference file index](https://2024.acmmm.org/files/) after local host
resolution failed. The call says regular submissions of different lengths use the
same review process with no long/short distinction. The file index lists the
accepted-ID text file, a full program PDF and a separate BNI call.

The browser response to the official `accepted_papers.txt` file was
content-encoded with Brotli; its decoded body is **5,497 bytes**, has **1,149
unique numeric IDs**, and matches the WORK-017 body SHA-256
`00441e7cd5f52a8030d6b5d316c66bae7707021fddb2a3647c3dd1e0d2c25fc2`. The
response headers and decoded body are in ignored
`reports/runs/WORK-2026-11-08-021/`. A direct local `curl` retry failed with exit
6 and HTTP status 000 because `2024.acmmm.org` did not resolve.

The official [BNI call](https://2024.acmmm.org/files/MM24_BNI.pdf) says accepted
BNI papers are full papers in the main proceedings, but uses a separate review
committee and criteria. The official [full program](https://2024.acmmm.org/files/MM24-Full_Program.pdf)
was converted to text through MarkItDown without retaining or hashing the origin
PDF. That diagnostic text contains 63 explicit `Paper <id>` labels; 60 IDs are
also in the accepted-ID file, three are outside it, and the program does not list
all 1,149 accepted IDs. The diagnostic is route evidence only, not an accepted
roster or complete proceedings join.

The official research-track statistics continue to report 1,150 acceptances. The
ID file, BNI call and partial program view do not resolve the one-record
discrepancy or establish the full publication set. Bulk metadata reuse terms
remain unverified. ACM Multimedia 2024 stays `access_unavailable` in roster v10;
no v11 roster, split, enrichment or graph state changed. See [D038](decisions.md#d038--acm-multimedia-2024-browser-source-follow-up-2026-11-08),
the [program audit artifact](../reports/runs/WORK-2026-11-08-021/acmmm2024_program_route_audit.json),
and [WORK-021](work-log/2026-11-08-021-acmmm-2024-browser-source-review.md).

## D034 MICCAI 2022 official source-route follow-up

The directly captured official Society accepted-paper index contains **573 unique
paper-detail links**; its topic-category page exposes 572 distinct linked records.
The prior v7 request returned HTTP 522, but the current direct retrieval succeeded
and both pages are hash-bound in [source corrections v9](../data/manifests/five-year-source-corrections-v9.json).

The official Springer proceedings comprise eight main volumes and 32 captured
contents pages with **576 unique chapter DOI records**. All eight volume pages
describe **574 revised full papers**; the refreshed series index still displays
576. A normalized-title comparison yields 558 unique exact-title pairs, leaving
15 Society records and 18 publisher chapters outside the exact-title join; three
publisher chapter titles are correction notices. No byline adjudication has been
done for the remaining title differences. The official program documents did not
provide a complete stable-ID roster that resolves the count conflict.

Therefore MICCAI 2022 remains **unresolved and ineligible**. The accepted index is
one record short of the publisher's full-paper claim, and no missing paper or
disposition is inferred. Roster v10, all frozen assignments, and the v2-bound
diagnostic/pregraph inputs are unchanged. Raw captures and program PDFs remain
ignored local artifacts; no per-record roster or paper PDF was published or
downloaded. See [D034](decisions.md#d034--miccai-2022-official-route-follow-up-2026-11-07)
and [WORK-007](work-log/2026-11-07-007-miccai-2022-source-followup.md).

Official routes: [MICCAI 2022 accepted papers](https://conferences.miccai.org/2022/papers/),
[topic categories](https://conferences.miccai.org/2022/papers/categories/),
[Springer proceedings, Part I](https://link.springer.com/book/10.1007/978-3-031-16431-6),
and the [Springer MICCAI index](https://link.springer.com/conference/miccai).

## ICLR official API access retry (WORK-009)

The official OpenReview v2 documentation describes querying notes with the
edition's submission invitation and paginated results. The official ICLR 2024
Conference group metadata is publicly readable and identifies
`ICLR.cc/2024/Conference/-/Submission` as its submission invitation. However, a
read-only request for the first note/count returned **HTTP 403
ChallengeRequiredError**. The current page remained on the group shell and did
not yield accepted-paper notes. A separate `/notes/search` query returned zero
results; that is not a population count and is not used as roster evidence.

No challenge verification was attempted. No complete roster was captured and no
edition or adapter status changed. All five ICLR years remain unresolved; the
prior 2024 count agreement and 2025 count discrepancy are unchanged. The
sanitized access-check hashes and outcomes are in the ignored
[WORK-009 route audit](../reports/runs/WORK-2026-11-07-009/openreview-route-audit.json).
The official [OpenReview API documentation](https://docs.openreview.net/reference/api-v2/openapi-definition),
[ICLR 2024 Conference group](https://openreview.net/group?id=ICLR.cc/2024/Conference),
and [WORK-009](work-log/2026-11-07-009-iclr-official-roster-access.md) document
the route and limitation.

## ICDM, ICRA and IROS official route review (WORK-010)

Official conference pages expose potential sources for these 15 edition
candidates, but the route review did not produce local, hash-bound complete
rosters or a full proceedings crosswalk. All 15 editions remain unresolved in
roster v10. The Search connector returned excerpts from some public pages; direct
local requests to the checked conference and PaperPlaza hosts failed DNS
resolution. The connector also refused PaperPlaza retrieval under its robots.txt
policy. No alternate access path, login, or restriction bypass was attempted.

For ICDM, official accepted-paper routes were found for 2021, 2024 and 2025;
the 2022 official program PDF and the 2023 official schedule/OpenReview group
are additional leads. The 2021 and 2024 pages distinguish Regular and Short
Papers. ICDM 2025 also has separate Regular and Short Papers sections, while its
call says submissions are not made to separate short/industrial/application
tracks. Official calls say accepted conference papers enter IEEE Computer
Society proceedings, and workshops have separate ICDMW proceedings. The
ICDM 2021 PhD Forum is another possible proceedings-bearing category whose
disposition under the main-research policy has not been verified. These page
sections and counts cannot be treated as a complete roster until every eligible
main category is reconciled to the corresponding IEEE Xplore volume and
out-of-scope proceedings are excluded. No access or redistribution terms for
bulk reuse of the extracted conference metadata were established in this check.
Year-specific leads are the [ICDM 2021 accepted list](https://icdm2021.auckland.ac.nz/accepted-papers/),
[2022 program PDF](https://www.cse.fau.edu/~xqzhu/icdm2022/ICDM2022Program.pdf),
[2023 schedule](https://www.cloud-conf.net/icdm2023/schedule.html) and
[OpenReview group](https://openreview.net/group?id=IEEE.org%2FICDM%2F2023),
[2024 accepted list](https://icdm2024.org/accepted_papers/), and
[2025 accepted list](https://www3.cs.stonybrook.edu/~icdm2025/acceptedpapers.html).

For ICRA 2021–2025, official conference materials point to PaperPlaza and, for
the 2022–2023 editions, the InfoVaya conference program/digest. The 2023 digest
states that access to its program and papers requires conference registration.
The program route is not itself a proceedings roster: official author materials
include journal-option presentations (including RA-L, T-RO and related venues),
which must be distinguished from papers accepted to the ICRA conference track.
The ICRA 2025 site links its detailed paper program through PaperPlaza. Year
leads include the [2021 PaperCept program](https://dev.papercept.net/conferences/conferences/xICRA21/program/),
[2022 program overview](https://ewh.ieee.org/soc/ras/conf/fullysponsored/icra/2022/icra2022.org/program/program-overview.html),
[2023 conference digest](https://events.infovaya.com/uploads/documents/events/103/215-A5DigestICRA2023-FINAL-copy-g.pdf),
[2024 program](https://2024.ieee-icra.org/program/), and
[2025 program](https://2025.ieee-icra.org/program/). No complete source capture,
permitted export, track-filtered list, or volume reconciliation was obtained.

For IROS, the official 2022 site reports 1,716 accepted papers and a 1,765-paper
final program that also includes 49 journal-publication presentations; it separately
reports late-breaking-result abstracts and workshops/tutorials. Its author guide
states that some journal-option papers appear in the event program but not in the
post-conference IEEE Xplore proceedings. The official IROS 2023 call explicitly
says late-breaking results are not publications and are not submitted to Xplore.
The 2024 and 2025 official program pages link to PaperPlaza. These boundaries
require edition-specific reconciliation against proceedings; neither program
counts nor a search-indexed excerpt is an eligible paper count. The 2021 complete
official program route was not captured; the [RSJ history page](https://www.rsj.or.jp/en/event/international/iros.html)
verifies the edition but does not supply its paper roster. Program leads include
[IROS 2022](https://iros2022.org/program/program-at-glance/),
[IROS 2023 PaperPlaza](https://ras.papercept.net/conferences/scripts/myprogram.pl?ConfID=401&PrinterFriendly=ON),
[IROS 2024 PaperPlaza](https://ras.papercept.net/conferences/scripts/myprogram.pl?ConfID=425),
and the [IROS 2025 official program notice](https://2025.ieee-iros.org/news).

Representative official routes: [ICDM 2021 accepted papers](https://icdm2021.auckland.ac.nz/accepted-papers/),
[ICDM 2024 accepted papers](https://icdm2024.org/accepted_papers/),
[ICDM 2025 accepted papers](https://www3.cs.stonybrook.edu/~icdm2025/acceptedpapers.html),
[ICDM 2023 schedule](https://www.cloud-conf.net/icdm2023/schedule.html),
[ICRA 2024 program](https://2024.ieee-icra.org/program/),
[ICRA 2025 program](https://2025.ieee-icra.org/program/),
[ICRA 2023 digest](https://events.infovaya.com/uploads/documents/events/103/215-A5DigestICRA2023-FINAL-copy-g.pdf),
[IROS 2022 program and counts](https://iros2022.org/program/program-at-glance/),
[IROS 2023 late-breaking-results policy](https://2023.ieee-iros.org/call-for-late-breaking-results/),
and [IROS 2025 program notice](https://2025.ieee-iros.org/news). These links
identify routes only; the v10 dispositions remain unchanged. See
[WORK-010](work-log/2026-11-07-010-ieee-edition-route-review.md).

## D033 MICCAI 2024 official 12-volume reconciliation (v10)

The Society's MICCAI 2024 accepted-paper page contains 856 numbered research
records. The complete official Springer main-proceedings set spans 12 volumes
and 49 captured contents pages, with 857 unique chapters. The Society roster
matches 856 distinct chapters: 836 exact-title and 20 unique title-and-byline
matches. The only unmatched chapter is a correction to a Society-listed paper;
it is excluded as nonresearch. MICCAI 2024 is eligible under the existing D015
policy. Workshop books remain outside the main-conference set.

The official [Society list](https://papers.miccai.org/miccai-2024/), [Springer
series index](https://link.springer.com/conference/miccai), and [main proceedings
set](https://link.springer.com/book/10.1007/978-3-031-72378-0) are hash-bound in
[source corrections v8](../data/manifests/five-year-source-corrections-v8.json).
Detailed pages and per-record rosters remain ignored local data. No PDFs or
per-record public roster were produced. See [D033](decisions.md#d033--miccai-2024-full-proceedings-reconciliation-2026-11-07),
[v10 recovery report](../reports/five-year-source-recovery-v10.md), and the
[v10 ledger](../reports/five-year-edition-ledger-v10.csv).

V10 has **98 eligible editions / 10 verified no-edition findings / 22 unresolved
roster/adapter editions / 40 access-unavailable editions**, with **94,857
observations: 91,355 included, 3,502 excluded, zero review**. The 62 incomplete
candidates keep P01 partial. All 76,629 guarded assignments, including 1,095
tests, remain preserved. P02 remains no-go for broader enrichment; the v2-bound
diagnostics/pregraph inputs remain unchanged.

## Historical D032 MICCAI roster closure and unresolved years (v9)

V9 overlays three MICCAI accepted-paper rosters on the immutable v8 baseline.
Official conference/Society lists contain 531 numbered records in 2021, 730 in
2023 and 1,027 in 2025; Springer year-book descriptions report matching full-paper
counts. The 2025 final Society update also reports 1,027 accepted papers. These
three editions are eligible under the existing main archival research-paper
policy. The 2021 and 2023 accepted lists expose titles and record IDs without
bylines; 2025 includes BibTeX names. None of these roster names/records alone
establishes a resolved person or accepted graph claim. D015 still requires an
authoritative detail byline before work matching or core-paper acceptance.

MICCAI 2022 remains unresolved: its official accepted-paper route returned HTTP
522, while the Springer volume description reports 574 revised full papers and
the series index displays 576. MICCAI 2024 also remains unresolved: the captured
Society list has 856 unique numbered records, while Springer reports 857 accepted
full papers and its index displays 857. The catalog counters are retained
separately and are not treated as accepted-paper counts. No missing record was
inferred or added. Detailed source captures and generated rosters remain ignored
local inputs; the tracked correction contains hashes, official links and aggregate
counts, with no per-record metadata or PDFs. See [D032](decisions.md#d032--miccai-roster-closure-and-unresolved-edition-counts-2026-11-07),
[source corrections v7](../data/manifests/five-year-source-corrections-v7.json),
[v9 recovery report](../reports/five-year-source-recovery-v9.md), and
[the v9 ledger](../reports/five-year-edition-ledger-v9.csv).

The measured ledger now has **97 eligible editions / 10 verified no-edition
findings / 23 unresolved roster/adapter editions / 40 access-unavailable editions**.
It contains **94,000 observations: 90,499 included and 3,501 excluded**. All
76,629 guarded assignments, including 1,095 tests, remain preserved. The 63
remaining candidates keep P01 incomplete; P02 remains no-go for broader
enrichment. The v2-bound diagnostics/pregraph frame is unchanged.

## Historical D030 route closure and COLING joint roster (v7)

Roster v7 applies direct official evidence to the 11 route rows that remained
unverified in v6. Ten are verified no-edition findings: ICCV 2022/2024; ECCV
2021/2023/2025; NAACL 2023; EACL 2022/2025; and COLING 2021/2023. COLING 2024
adds the official joint LREC-COLING proceedings, assigned once to COLING with an
LREC co-host crosswalk. See [source correction v5](../data/manifests/five-year-source-corrections-v5.json),
[v7 recovery report](../reports/five-year-source-recovery-v7.md), and the
[v7 edition ledger](../reports/five-year-edition-ledger-v7.csv). The full scope
ledger now has **90 eligible editions / 10 verified no-edition findings / 30
unsupported adapters / 40 access-unavailable editions**. The 70 incomplete
candidates remain coverage failures.

## D031 AAMAS official rosters and 2023 reconciliation hold (v8)

The official [IFAAMAS proceedings index](https://www.ifaamas.org/proceedings.html)
links complete AAMAS proceedings contents for 2021–2025. V8 applies D015's
existing main-research policy to four explicit year-specific categories: Main
Track (2021 and 2022), Full Research Papers (2024), and Research Paper Track
(2025). These four editions are eligible; all other enumerated contents sections
remain excluded. They add **807 included records** across the four rosters. The
complete counts and official contents-page links are in the
[v8 recovery report](../reports/five-year-source-recovery-v8.md) and
[v8 ledger](../reports/five-year-edition-ledger-v8.csv).

AAMAS 2023 remains unresolved. Official news announces 237 full papers and 221
extended abstracts, while the accepted-paper page lists 237 and 219. An automated
exact-title join maps 225/237 full-paper titles to the official proceedings
contents; 12 titles differ, and 35 of the exact-title matches have different
author strings. These joins have not been adjudicated and do not establish
publication-ID/byline identity. No 2023 AAMAS roster rows were added.

The proceedings notices allow limited personal/classroom copying with attribution
and require permission or a fee for republication/redistribution. Detailed pages
and rosters remain in ignored local storage; the tracked correction contains
source URLs, response hashes and aggregate dispositions only. No PDFs were
downloaded. See [D031](decisions.md#d031--aamas-official-roster-closure-and-2023-reconciliation-hold-2026-11-07)
and [source correction v6](../data/manifests/five-year-source-corrections-v6.json).

### AAMAS 2023 follow-up (WORK-005)

The official accepted full-paper page lists 237 records, matching the official
news count. The same page lists 219 extended abstracts, while official news says
221. The conservative exact normalized-title diagnostic joins **225/237** full
papers to the official proceedings contents; **12** titles remain unmatched and
**35** of the exact-title joins have byline differences. No exact-title join is
ambiguous. The separate official author index contains 471 PDF-link occurrences
for 316 distinct IDs, including 154 distinct IDs labeled Main Track Full Paper;
it is not a complete accepted-paper identifier bridge. These sources do not close
the full-paper to proceedings-ID reconciliation, so AAMAS 2023 remains unresolved.
No rows were added. Original captures remain hash-bound under source correction
v6; see [WORK-005](work-log/2026-11-07-005-aamas-2023-reconciliation.md).

### AAMAS 2023 official identifier scan (WORK-008)

On 7 November, all six hash-bound AAMAS 2023 sources in source-corrections v6
were rechecked. The accepted full-paper entries expose no per-entry record link,
ID attribute or DOI. The official proceedings contents contain 528 PDF links
with local `p...` identifiers and no DOI links, but the accepted page does not
map its entries to those identifiers. The official author index remains
incomplete: 471 PDF-link occurrences across 316 record IDs, with 154 IDs labeled
Main Track Full Paper.

An aggregate exact ordered-byline comparison produces 196 unique author-only
candidate joins, of which 190 also have an exact normalized-title match and six
have a different title. Forty accepted entries have no byline candidate and one
has multiple candidates. These are candidate joins only, not adjudicated record
identities. Combined with the 12 title gaps and 35 byline differences among the
225 exact-title joins, the full accepted-paper to proceedings-ID crosswalk remains
incomplete. No per-record metadata was added to the tracked report, and no 2023
roster rows were added. Roster v10 and all frozen assignments remain unchanged;
see [WORK-008](work-log/2026-11-07-008-aamas-2023-followup.md).

## ICLR official route and roster-access check (WORK-003)

The official [OpenReview venue index](https://openreview.net/venue?id=ICLR.cc)
lists separate ICLR Conference groups for 2021–2025, alongside year-specific
workshops, blog tracks and other side venues. ICLR's [proceedings FAQ](https://iclr.cc/FAQ/Proceedings)
says accepted papers from 2013–2025 are accessed through OpenReview. The current
[electronic-proceedings index](https://proceedings.iclr.cc/papers/) separately
lists ICLR 2024–2026.

The [official ICLR 2024 proceedings book](https://proceedings.iclr.cc/paper_files/paper/2024)
lists 2,260 papers, matching the [official 2024 fact sheet](https://media.iclr.cc/Conferences/ICLR2024/ICLR2024-Fact_Sheet.pdf)'s
2,260 accepted count. The [2025 proceedings book](https://proceedings.iclr.cc/paper_files/paper/2025)
lists 3,703 papers; the currently hosted [2025 draft fact sheet](https://media.iclr.cc/Conferences/ICLR2025/ICLR2025_Fact_Sheet.pdf)
reports 3,704 accepted. This difference is unresolved. The 2021–2023 official
route remains OpenReview; the electronic-proceedings index does not list those
years as books.

The [ICLR FAQ](https://iclr.cc/FAQ) says authors keep copyright and grant ICLR a
license to copy, distribute and display their papers. That statement does not
establish permission to republish this project's per-record roster. No paper
PDFs or ICLR per-record roster were downloaded, captured, or published.

During WORK-003, a direct local request to the OpenReview API returned HTTP 403
(315-byte response). A local request for the 2024 proceedings page failed DNS
resolution (`curl` exit 6). Remote search-service page views did not create a
hash-bound local source capture. Therefore no ICLR edition was promoted and no
roster records were added. All five ICLR years remain unresolved pending complete
locally accessible official inputs, per-year main-track reconciliation and
versioned replay. No PDFs were downloaded.

## ICAPS 2025 track correction

The official [ICAPS 2025 main technical call](https://icaps25.icaps-conference.org/calls/main_track/)
lists theoretical, algorithmic, modelling, position, and tools submissions under
the main technical call. Its [program committee policy](https://icaps25.icaps-conference.org/organisation/roles_and_guidelines/)
says 2025 uses topics rather than tracks, following the single-track structure
introduced for 2024. The [official accepted-paper list](https://icaps25.icaps-conference.org/program/accepted/)
links to the publisher records.

The cached OJS issue has 52 article records. The accepted page had 56 links because
papers appear under multiple keyword headings, yielding 51 distinct publisher
article IDs. All 48 v5 records in theoretical, algorithmic, modelling, and tools
sections match accepted publisher IDs exactly. They are now included in roster
v6. Three accepted position papers remain excluded under the project's existing
main archival research-paper policy; frontmatter remains excluded. No scope or
quality-threshold decision changed. The 2025 edition now has 48 included, four
excluded, and zero review records.

The tracked correction record is
[`five-year-source-corrections-v4.json`](../data/manifests/five-year-source-corrections-v4.json).
It records the 52 issue IDs, 48 accepted main-research IDs, three position IDs,
frontmatter ID, original issue-response hash, and the hash of the captured accepted
link extraction. The extracted link JSON is retained under the ignored task run
directory; its hash is not a raw webpage-body hash. The original v5 roster and
failed/full readiness history remain intact.

## Other prioritized source routes

| Family | Official route evidence | Status after this check |
| --- | --- | --- |
| ICLR | [OpenReview venue index](https://openreview.net/venue?id=ICLR.cc) and [ICLR Proceedings FAQ](https://iclr.cc/FAQ/Proceedings) identify official 2021–2025 Conference groups and accepted-paper access through OpenReview; a separate electronic-proceedings index lists 2024–2026. | Official routes verified. The 2024 book/fact-sheet counts agree at 2,260; the 2025 book/draft-fact-sheet counts differ (3,703/3,704). Local API returned HTTP 403 and local proceedings access failed DNS; no hash-bound full roster, so all five years remain unresolved. See WORK-003. |
| MICCAI | [Springer proceedings index](https://link.springer.com/conference/miccai), year-specific Society accepted/open-access pages, and official Springer book descriptions. | V10 closes 2021 (531), 2023 (730), 2024 (856 accepted papers reconciled against 857 chapters, one correction excluded), and 2025 (1,027). MICCAI 2022 remains unresolved (522 route failure; 574 full papers / 576 index counter). Index counts remain distinct from accepted-paper totals. |
| AAMAS | The [IFAAMAS proceedings index](https://www.ifaamas.org/proceedings.html) links official proceedings for 2021–2025. | V8 resolves 2021, 2022, 2024 and 2025 using their named main-research sections. AAMAS 2023 remains unresolved pending title/author/publication-ID reconciliation. Redistribution restrictions remain; see D031. |

The official [IEEE Xplore publisher index](https://ieeexplore.ieee.org/Xplore/home.jsp)
also exposes individual records for all five target years in ICDM, ICRA, and IROS.
For example, see ICDM [2021](https://ieeexplore.ieee.org/document/9679138/),
[2022](https://ieeexplore.ieee.org/document/10027698/),
[2023](https://ieeexplore.ieee.org/document/10415678/),
[2024](https://ieeexplore.ieee.org/document/10884330/), and
[2025](https://ieeexplore.ieee.org/document/11392077/); ICRA
[2021](https://ieeexplore.ieee.org/document/9561002/),
[2022](https://ieeexplore.ieee.org/document/9811561/),
[2023](https://ieeexplore.ieee.org/document/10161283/),
[2024](https://ieeexplore.ieee.org/document/10610761/), and
[2025](https://ieeexplore.ieee.org/document/11127489/); and IROS
[2021](https://ieeexplore.ieee.org/document/9636575/),
[2022](https://ieeexplore.ieee.org/document/9981855/),
[2023](https://ieeexplore.ieee.org/document/10342313/),
[2024](https://ieeexplore.ieee.org/document/10801967/), and
[2025](https://ieeexplore.ieee.org/document/11246923/). These are representative
publisher records, not complete volume rosters or proof of accepted-track
coverage. The per-year official contents, special/workshop volume boundaries,
rights, pagination, and complete counts remain to be captured and reconciled
before any of these 15 rows can become eligible.

No complete-roster claim or new eligibility disposition was added for ICLR,
ICDM, ICRA or IROS by this route triage. ICLR's official routes and 2024–2025
proceedings counts are documented, but no ICLR roster is locally complete.
AAMAS 2021, 2022, 2024 and 2025 are eligible in v8; 2023 remains unresolved.
MICCAI has four eligible years in v10 and one unresolved year. See the [v10 measured ledger](../reports/five-year-edition-ledger-v10.csv)
for current dispositions, the [v7 report](../reports/five-year-source-recovery-v7.md)
for route closure, and the [v6 report](../reports/five-year-source-recovery-v6.md)
for the earlier route investigation.

## ACM and SIAM official route review (WORK-011)

The Search connector rendered selected official conference-hosted accepted-paper
and program pages. A fresh local HTTP check failed DNS for the official ACM
Multimedia 2024, CIKM 2025 and RecSys 2025 hosts; the other seven ACM/SIAM and
conference domains checked in WORK-011 also failed. Search-service access to the
SIAM 2025 proceedings DOI and the ACM Web Conference 2024 ACM Digital Library
proceedings returned **403 Forbidden**. These web-rendered pages are route evidence,
not locally captured source bodies or complete, hash-bound rosters. No restricted
publisher route was retried or bypassed, and access or reuse permission is not
inferred from a public conference page.

Selected route findings:

| Venue/years | Official route lead | Boundary or unresolved check |
| --- | --- | --- |
| KDD 2021, 2023–2025 | Official accepted-paper or Research Track Papers pages exist; KDD 2025 has separate Research and Applied Data Science tracks and two submission cycles | KDD 2025 accepted papers span two proceedings volumes; full counts and edition-to-volume reconciliation are not locally captured |
| The Web Conference 2022, 2024 | Official accepted pages separate Research Tracks from short, industry, Web4Good, resource and other categories. The 2024 page points to OpenReview and ACM proceedings and states that SIGWEB offers free access | The 2024 public acceptance figure combines several tracks; a research-only count and complete proceedings crosswalk were not locally verified. Free access does not establish bulk metadata reuse rights |
| SIGIR 2021–2024 | Official accepted-paper/program routes include full-paper sections; SIGIR 2024 identifies full, short, resource/reproducibility, perspective, doctoral, demonstration and industry categories | Full-paper denominators and proceedings records still need year-by-year closure; SIGIR 2025 has no captured route in this scan |
| WSDM 2021–2023, 2025 | Official accepted research/paper pages exist; WSDM 2025 has a separate accepted-demonstrations page | WSDM 2024 and all five complete proceedings reconciliations remain open |
| RecSys 2022, 2024–2025 | Official accepted-contribution pages separate long/full papers from short, reproducibility, industry, late-breaking, demo and doctoral material | Labels and main-research eligibility differ by year; no complete list or proceedings crosswalk is locally captured |
| CIKM 2021 and 2025 | Official accepted pages distinguish Full Research, Short Research, Applied Research, Resource, Demo and PhD/Industry categories; the 2025 program identifies Full Research (FP) and Applied Research (ARS) tracks | The project's disposition of applied research must follow the existing venue policy; the complete accepted-to-proceedings frame and local source capture are missing |
| ACM Multimedia 2021, 2024 | Official regular-paper pages exist; the 2024 conference file index lists `accepted_papers.txt` | The Search-service text rendering of that file showed 1,149 numeric lines, while the ACM MM main site reports 1,150 accepted 2024 papers. The file was not retrieved locally and its schema/count cannot be verified; treat this as a lead, not an established discrepancy or roster count. The accepted-list page renders a JavaScript shell through Search |
| SIAM SDM 2023, 2025 | Official SDM 2023 proceedings front matter reports 105 research papers plus about half a dozen Blue-Sky idea papers. The 2025 SIAM site has an Accepted Papers page and a Program & Abstracts page linking its proceedings | The 2025 accepted list includes Blue-Sky labels within the same page; the proceedings DOI fetch returned 403. Neither year has a complete locally captured main-research roster |

Official route links: [KDD 2021 accepted papers](https://kdd.org/kdd2021/accepted-papers/index.html),
[KDD 2024 Research Track papers](https://www.kdd.org/kdd2024/research-track-papers/),
[KDD 2025 Research Track papers](https://kdd.org/kdd2025/research-track-papers-2/),
[TheWebConf 2022 accepted papers](https://archives.iw3c2.org/www2022/accepted-papers/),
[TheWebConf 2024 Research Tracks](https://www2024.thewebconf.org/accepted/research-tracks/),
[SIGIR 2021 accepted papers](https://sigir.org/sigir2021/accepted-papers/),
[SIGIR 2022 accepted papers](https://sigir.org/sigir2022/program/accepted/),
[SIGIR 2023 full papers](https://sigir.org/sigir2023/program/accepted-papers/full-papers/),
[SIGIR 2024 accepted papers](https://sigir-2024.github.io/program_papers.html),
[WSDM 2021 accepted research papers](https://www.wsdm-conference.org/2021/accepted-papers.php),
[WSDM 2022 accepted papers](https://www.wsdm-conference.org/2022/accepted-papers/),
[WSDM 2023 accepted papers](https://www.wsdm-conference.org/2023/program/accepted-papers),
[WSDM 2025 accepted papers](https://www.wsdm-conference.org/2025/accepted-papers/),
[RecSys 2022 accepted contributions](https://recsys.acm.org/recsys22/accepted-contributions/),
[RecSys 2024 accepted contributions](https://recsys.acm.org/recsys24/accepted-contributions/),
[RecSys 2025 accepted contributions](https://recsys.acm.org/recsys25/accepted-contributions/),
[CIKM 2021 accepted papers](https://www.cikm2021.org/accepted-papers),
[CIKM 2025 accepted papers](https://www.cikm2025.org/program/accepted-papers),
[ACM MM 2021 regular papers](https://2021.acmmm.org/regular-papers),
[ACM MM 2024 regular papers](https://2024.acmmm.org/regular-papers),
[ACM MM 2024 accepted-paper ID file](https://2024.acmmm.org/files/accepted_papers.txt),
[ACM MM acceptance statistics](https://www.acmmm.org/),
[SDM 2023 proceedings front matter](https://epubs.siam.org/doi/pdf/10.1137/1.9781611977653.fm),
[SDM 2025 accepted papers](https://www.siam.org/conferences-events/past-event-archive/sdm25/program/accepted-papers/),
[SDM 2025 program and proceedings link](https://www.siam.org/conferences-events/past-event-archive/sdm25/program/program-abstracts/),
and [WORK-011](work-log/2026-11-07-011-acm-siam-source-route-review.md).

### ACM Multimedia 2024 official source follow-up (WORK-017)

Read-only fetches captured three official conference-hosted pages. The
`accepted_papers.txt` file is 5,497 bytes (SHA-256
`00441e7cd5f52a8030d6b5d316c66bae7707021fddb2a3647c3dd1e0d2c25fc2`) and has
1,149 unique numeric values, no duplicates, and a final newline. This verifies
the file's contents and shape only; its numeric-ID schema and completeness are
not defined by the file itself.

The official ACM Multimedia statistics page labels its table “Research Track
Statistics” and gives the 2024 row as 4,385 submissions, 1,150 acceptances and a
26.20% acceptance ratio. The 43,256-byte local capture has SHA-256
`1b3428b0a898f66dc92a5bd517f882d06dada0164d805cabae627107cda05a47`. The official
2024 regular-papers URL returned a 7,508-byte JavaScript application shell with
SHA-256 `24131a90c6f898357a100157e932bbc6e8d2c0651c6075207bcad09e71eae544`; it
contains no roster records. Subsequent requests for its public JavaScript assets
failed local DNS resolution. The official `/files/` index lists a full program
PDF, and Search renders it as five pages, but no local hash-bound copy or full
paper-level crosswalk was obtained.

Search also renders the official regular-paper call as one research-paper track
with the same review process regardless of paper length. A separate official
Brave New Ideas call says accepted BNI papers appear in the main proceedings.
These track statements are leads only: the conference ID file does not document
whether it covers BNI, and neither view provides an accepted-to-proceedings join.
No evidence currently decides whether BNI belongs under the existing
`main_archival_research_papers` policy. Bulk metadata reuse terms are unverified;
no publisher restriction was bypassed.

Official routes: [accepted-paper ID file](https://2024.acmmm.org/files/accepted_papers.txt),
[regular-paper call](https://2024.acmmm.org/regular-papers),
[Brave New Ideas call](https://2024.acmmm.org/files/MM24_BNI.pdf),
[full program](https://2024.acmmm.org/files/MM24-Full_Program.pdf),
[conference file index](https://2024.acmmm.org/files/), and
[research-track statistics](https://www.acmmm.org/).

Therefore ACM Multimedia 2024 remains `access_unavailable` in roster v10. Do not
infer that the ID list omits exactly one paper, treat the statistics count as a
roster, or include/exclude BNI from a count difference. No v11 roster or source
correction was created. The 42 v10 output hashes and five configured frozen-input
hashes verify; 76,629 assignments, including 1,095 tests, remain unchanged. P01
still has 62 incomplete candidates. P02 remains no-go: one reviewer is reported,
available hours are unknown, and a second independent reviewer is unconfirmed.
Raw captures are ignored under
`reports/runs/WORK-2026-11-07-017/`; no per-record IDs, paper PDFs, enrichment,
split, graph or database output was created. See [D035](decisions.md#d035--acm-multimedia-2024-official-source-hold-2026-11-07)
and [WORK-017](work-log/2026-11-07-017-p01-acmmm-2024-source-closure.md).

This route scan does not reduce the **40 publisher-access-unavailable** candidates
or change any edition disposition. The 22 unresolved roster/adapter candidates,
all v10 counts and every frozen assignment remain unchanged.

## ICDM 2021 official accepted-list follow-up (WORK-018)

The official ICDM 2021 [accepted-paper page](https://icdm2021.auckland.ac.nz/accepted-papers/)
contains **197 unique DM IDs**: 98 under Regular Papers and 99 under Short
Papers. All 197 appear in the official [conference schedule](https://icdm2021.auckland.ac.nz/calendar/conference-schedule/).
The schedule has 239 unique DM IDs total; its 42 additional IDs are scheduled in
named workshop events (40) or a separate PhD Panel event (2). The separate
[PhD Forum call](https://icdm2021.auckland.ac.nz/call-for-phdforum/) describes
doctoral submissions and says accepted papers appear in IEEE proceedings, but
the two PhD Panel records were not individually linked to those proceedings. The
official [conference call](https://icdm2021.auckland.ac.nz/cfp/) says its
accepted papers appear in IEEE Computer Society proceedings and describes one
submission process without separate short-paper submissions; the accepted page's
Regular/Short labels are preserved as published.

| Official capture | Bytes | SHA-256 | Use in this review |
| --- | ---: | --- | --- |
| Accepted-paper page | 122,225 | `8f51feda2b75e73788b641dd273d67183fef6ee4a91cae107a955c8a2bd51598` | 197-entry conference roster and its two labels |
| Conference schedule | 299,539 | `6cc5cee0cdded5136743f17323b647ec7b5b8d60d3ed690c4c26777e1b4a364d` | All 197 accepted IDs appear; 42 others are in separately named events |
| Conference call | 97,039 | `8f32caca80fbb71edd179dd8fbd91e8f59b3ac8b8766a79dd37a4e18a13e792a` | IEEE Computer Society proceedings statement and submission structure |
| PhD Forum call | 90,673 | `d20844b4a7dabca634aac3337f4d6bc06bd823c1b4e3e14e5699178be2cae8e5` | Separate doctoral route and its proceedings statement |
| University copyright page | 197,134 | `5ba52eb97014cfca479f8305ec742ac7baac3deeba7608e5ecb765e924695e48` | [University/third-party reuse distinction](https://www.auckland.ac.nz/en/admin/footer-links/copyright.html) |

A local request for the IEEE Xplore proceedings page returned **HTTP 418**; no
restriction bypass was attempted. The official conference pages do not provide a
complete paper-level proceedings crosswalk. The [University copyright terms](https://www.auckland.ac.nz/en/admin/footer-links/copyright.html)
allow specified use for material clearly owned by the University but direct users
to obtain authorization for third-party material; the captured conference pages
do not establish the ownership or bulk reuse permission for these paper records.
Therefore ICDM 2021 remains **unresolved** and ineligible in roster v10. No v11
roster or source-correction overlay was created. The 42 schedule-only IDs are not
added to the accepted roster, and no per-record metadata or paper PDFs are
published. Roster v10 and all 76,629 frozen assignments remain unchanged; P01
still has 62 incomplete candidates, and P02 remains no-go. Raw captures are
ignored under `reports/runs/WORK-2026-11-07-018/`. See [D036](decisions.md#d036--icdm-2021-official-source-hold-2026-11-07)
and [WORK-018](work-log/2026-11-07-018-icdm-2021-source-closure.md).

## CIKM 2025 proceedings-route follow-up (WORK-012)

The Search connector rendered the official accepted-paper list and the separate
conference-hosted proceedings page. Its view labels Full Research, Short Research,
Applied Research, Resource, Demo and PhD Symposium categories; the proceedings
page contains article links to ACM Digital Library records. This gives a stronger
official accepted-to-proceedings route for CIKM 2025, but Search-rendered text is
not a local source capture, its output cannot substitute for a source hash, and
complete paper-level reconciliation was not performed. Under the existing
`main_archival_research_papers` policy, the separate Applied Research category
remains for review; no new track decision was made.

The official pages are [CIKM 2025 accepted papers](https://www.cikm2025.org/program/accepted-papers)
and [CIKM 2025 proceedings](https://cikm2025.org/program/proceedings). The Search
connector reported a 9,257-line proceedings view with Full Research, Short,
Applied, Resource, Demo and PhD Symposium session headings. This is route evidence
only. No CIKM roster version or edition disposition changed. The Site source helper
also failed before checkout because its Git host did not resolve; no Site push or
publication occurred. See [WORK-012](work-log/2026-11-07-012-pregraph-source-followup.md).

## CIKM 2025 local source recapture recheck (WORK-019)

The Search connector again opened the official [accepted-paper page](https://www.cikm2025.org/program/accepted-papers)
and [proceedings page](https://cikm2025.org/program/proceedings), plus the venue's
[Full Research](https://www.cikm2025.org/calls/full-research-papers) and
[Short Research](https://www.cikm2025.org/calls/short-research-papers) calls. The
accepted-page view identifies Full, Short, Applied, Resource, Demo, PhD Symposium,
and Industry Day categories. These are Search-rendered views, not preserved origin
responses: they supply no source-byte hashes and no complete record-level
reconciliation. The distinct Applied category remains for review under the
existing `main_archival_research_papers` rule; no track decision is inferred.

The current local DNS scan extracted **55 unique URL hosts** from
`configs/conference-scope-2021-2025.yaml` and this source-triage file; **0/55
resolved**. Direct `curl` requests for both CIKM pages exited **6** with HTTP status
`000`, returning no bytes. The exact host list, request outcomes and sanitized
Search-access metadata are in ignored
`reports/runs/WORK-2026-11-07-019/`. CIKM 2025 stays unresolved in v10; no source
correction, roster, split, enrichment or graph state changed. This check does not
resolve publisher reuse terms. See [WORK-019](work-log/2026-11-07-019-p01-cikm-2025-source-recheck.md).

## CIKM 2025 browser source capture (WORK-022)

The connected browser captured HTTP 200 responses and response headers for the
official [accepted-paper page](https://www.cikm2025.org/program/accepted-papers),
[proceedings page](https://www.cikm2025.org/program/proceedings), and the
[Full Research](https://www.cikm2025.org/calls/full-research-papers),
[Short Research](https://www.cikm2025.org/calls/short-research-papers), and
[Applied Research](https://www.cikm2025.org/calls/applied-research-papers) calls.
Body/header hashes and ignored raw captures are listed in
[source corrections v12](../data/manifests/five-year-source-corrections-v12.json).

The accepted page has **827 unique IDs** across seven categories: **436 Full
Research, 185 Short Research, 93 Applied Research, 52 Resource, 37 Demo, 11 PhD
Symposium, and 13 Industry Day**. Full and Short are candidate research tracks
under the existing `main_archival_research_papers` policy. The separate Applied
Research call says it is unlike the Research Track and centers applied systems,
data acquisition, or measurable real-world impact; no project-specific track
decision was made.

The proceedings page links to **852 unique ACM Digital Library records** under
one DOI collection prefix (`10.1145/3746252`) and does not expose the accepted
page's IDs. NFKC/casefold/punctuation-normalized titles match **789** accepted
records; **38** accepted titles have no exact proceedings-title match, and **63**
publisher titles have no exact accepted-title match. Exact title plus author-set
comparison matches 697 accepted records overall and 531 Full/Short records.
These are aggregate candidate counts only; title/byline variations were not
adjudicated into a complete record-level crosswalk. The Full and Short calls
require an author to register and present accepted work on-site for proceedings
inclusion. Captured pages carry an all-rights-reserved footer and give no
metadata license or bulk-reuse authorization.

CIKM 2025 remains **`access_unavailable`** in roster v10. No v11 roster, track disposition,
or per-record metadata was created. Keep raw source captures ignored, publish
aggregate counts and official links only, and preserve every frozen assignment.
See [D039](decisions.md#d039--cikm-2025-browser-source-audit-2026-11-08),
[source corrections v12](../data/manifests/five-year-source-corrections-v12.json),
and [WORK-022](work-log/2026-11-08-022-cikm-2025-browser-source-capture.md).

## P01 and P02 handoff

P01 remains incomplete: **62 of 170 edition candidates** still lack complete
eligible rosters (22 unresolved roster/adapter editions and 40 access failures).
The 22 comprise 21 source/adapter gaps across ICLR, MICCAI 2022, ICDM, ICRA and
IROS, plus AAMAS 2023's unresolved reconciliation. ICDM 2021 now has a captured
accepted list and schedule comparison (WORK-018), but the proceedings crosswalk
and metadata reuse rights remain unresolved. CIKM 2025 now has hash-bound official
accepted, proceedings, and three call-page captures (WORK-022), but its 827-entry
accepted list does not reconcile to the 852 linked proceedings records and source
reuse terms remain unestablished. The full/short research crosswalk and Applied
Research disposition remain open.
Roster v10 is a partial source-correction iteration, not complete five-year scope
closure. P02 is
a **no-go for broader enrichment** until a complete eligible frame, canonical work
count, prospective P03 design, live free-resource limits, storage budget, and
actual reviewer capacity are known. The current enrichment/request budget remains
zero; this is a stop decision, not a full-release cost forecast.
