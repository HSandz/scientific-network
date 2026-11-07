# Official edition closure v7 — route evidence and COLING 2024

**Recorded:** 7 November 2026, Asia/Bangkok (UTC+07:00)
**Method:** `five-year-official-rosters-v7`
**Configuration:** [`corpus-five-year-v7.yaml`](../configs/corpus-five-year-v7.yaml)
**Correction evidence:** [`five-year-source-corrections-v5.json`](../data/manifests/five-year-source-corrections-v5.json)
**Decision:** [D030](../docs/decisions.md#d030--official-route-closure-and-coling-joint-edition-mapping-2026-11-07)

Roster v7 applies official edition-history findings to the 11 route candidates
that remained unverified after v6. Ten candidates are now verified no-edition
findings. The official LREC-COLING 2024 proceedings add one eligible joint-event
roster under COLING, with the LREC co-host recorded as a crosswalk. The previous
v1–v6 artifacts, v2-bound diagnostic inputs, all assignments, scope, schema and
quality thresholds remain preserved. This is roster discovery only: it performs
no split, paper enrichment, identity resolution, graph construction or database
write.

## Measured roster

| Measure | v7 result |
| --- | ---: |
| Venue-year candidates retained | 170 |
| Eligible editions | 90 |
| Verified no-edition findings | 10 |
| Unsupported-adapter editions | 30 |
| Publisher-access-unavailable editions | 40 |
| Incomplete edition candidates | 70 |
| Roster observations | 90,163 |
| Included | 87,404 |
| Excluded | 2,759 |
| Record-level review | 0 |
| Frozen assignments guarded | 76,629 |
| Protected test assignments | 1,095 |

| Conference year | Roster observations |
| --- | ---: |
| 2021 | 12,794 |
| 2022 | 13,925 |
| 2023 | 16,138 |
| 2024 | 21,666 |
| 2025 | 25,640 |

The v7 method inherits the v6 roster and applies the hash-bound corrections to
the 11 previously unverified candidates. These are bibliographic observations,
not canonical works, graph nodes, accepted edges or semantic-accuracy results.
The 30 unsupported-adapter and 40 access-unavailable editions remain incomplete;
their absence from this count does not mean they have no papers.

## Official edition evidence and joint-event mapping

The correction manifest records official evidence URLs, retrieval dates, response
metadata and hashes. The [COLING 2025 FAQ](https://coling2025.org/faqs/) describes
the series' move to odd years and the one-time LREC-COLING 2024 event. The official
[COLING archive](https://aclanthology.org/venues/coling/) has no 2021 or 2023
edition. The official [EACL conference history](https://eacl.org/conferences/)
lists ACL 2022 in EACL's place and has no 2025 EACL entry. The official
[ECCV 2024 page](https://eccv.ecva.net/Conferences/2024) describes its even-year
cadence; the [CVPR/ICCV Steering Committee bylaws](https://www.thecvf.com/docs/CVPR%20ICCV%20bylaws%20final.pdf)
state that ICCV is held in odd-numbered years. For NAACL 2023, the official
[ACL 2023 handbook](https://2023.aclweb.org/downloads/acl2023-handbook-v3.pdf)
states there was no NAACL because ACL was held in North America, consistent with
the [NAACL conference history](https://naacl.org/conferences/).

These sources support the following ten no-edition dispositions: ICCV 2022/2024;
ECCV 2021/2023/2025; NAACL 2023; EACL 2022/2025; and COLING 2021/2023. The COLING
2024 source is the official [LREC-COLING proceedings volume](https://aclanthology.org/volumes/2024.lrec-main/).
Its 1,555 records comprise 1,554 papers and one volume-frontmatter record. The
papers are assigned once to primary series `venue:coling`, event
`event:lrec-coling:2024`, with `venue:lrec` retained in the joint-event crosswalk;
front matter remains excluded. No LREC series or duplicate paper records are
added.

## Reproduction and checks

The v7 configuration SHA-256 is
`59e4edc3fad111e7d8eb5f32833697b5d13dda218d572e653230e91be1b41b75`; the source
correction SHA-256 is
`63a02fdd27fcf296fa0291d6b257124d202ff4d2fe16e4abf7895e401683b1fe`. The
correction manifest binds the COLING source response SHA-256
`cf988002de62da2c6d0231be7b97daab3f16c771cdb55d0351526343e34ca158` and the
captured pre-overlay roster SHA-256
`6de4850b48acbf785603c4c4fbff99a143fdc0591b35f0e63071bad08df0373e`. After
the joint-event fields are applied, the output COLING roster SHA-256 is
`da1a0ddce689145d45ee5489ac79545c95423904c77e930dcb2c4573aede3e68`.

The discovery command was replayed against a fresh temporary output using the
hash-bound local inputs. It returned **exit 1 as designed** because 70 edition
candidates remain incomplete. The replay matched every recorded v7 output hash;
the existing v7 output tree also matched all recorded hashes. The COLING ledger
roster hash matches its output roster. The full offline suite passed: **187 tests**.
These checks validate the pipeline contract and deterministic outputs; they do not
provide independent scientific review of every inherited edition.

| Artifact | SHA-256 |
| --- | --- |
| Roster manifest | `7e9b6874f6773df7cb16dc7c87594bddeae697d6c1b9439e69217d7f0f18a5f4` |
| Edition ledger | `a94a32ef87ff2b48aeba8f45eb50d0c24f8ec2a2a2ac2a57fc0561c2fffa159d` |
| 170-row CSV ledger | `95795fa9ca9c2ec03d50f37b995efbc4ab9702a2828ed61e4da9675ef9bdfd36` |

The revalidated assignment guard covers all **76,629** frozen assignments,
including **1,095** held-out test assignments. No new split or canonical work
merge was created. Discovery recorded zero enrichment requests and zero graph
writes. The five-year semantic accuracy, recall and coverage remain unmeasured.

## Remaining limits and next work

P01 remains incomplete because 30 editions still need supported official roster
adapters and 40 editions remain access-unavailable. The source-route notes in
[`five-year-source-triage.md`](../docs/five-year-source-triage.md) distinguish
official leads from complete eligible rosters. Source rights and redistribution
must be checked per route; an official proceedings page alone does not grant a
redistribution right.

The COLING capture referenced by the correction manifest is under ignored
`reports/runs/WORK-2026-11-07-001/`; the raw official response snapshots are under
ignored `data/raw/five-year-source-cache-v7/`. The replay was reproducible in this
workspace, but those ignored inputs are not a clean-checkout reproduction bundle
and must be reacquired or separately archived under permitted terms.

P02 remains **no-go for broader enrichment**. The complete eligible frame,
canonical-work population, prospective P03 design, current free-resource/storage
limits and actual reviewer capacity are not measured. No broader metadata, ORCID,
PDF, model or annotation requests are authorized by this checkpoint. The v2-bound
diagnostic and pregraph artifacts remain historical and are not refreshed by v7.
Independent component accuracy, recall, F1 and release readiness remain
unmeasured or failed.

See the [current 170-row ledger](five-year-edition-ledger-v7.csv),
[aggregate metrics](five-year-source-recovery-v7.metrics.json),
[source triage](../docs/five-year-source-triage.md), and
[current status](../docs/status.md).
