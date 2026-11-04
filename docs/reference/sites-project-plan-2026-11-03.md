# AI Research Network Project Specification

**Course:** Social Media Network Analysis for Business  
**Project:** International Network of AI Researchers and Research Organizations  
**Specification date:** 1 November 2026; scope revised 3 November 2026  
**Team:** Two people

**Schedule:** Original eight-week baseline; expanded workload must be re-estimated

**Current instruction:** Planning only. No new research-data collection is authorized.
NeurIPS and ICML were course examples, not the intended limit of the network.

## 1 Project decision and acceptance criteria

**Build an evidence-backed academic social network in Neo4j.** Connect researchers, organizations, papers, topics and venues through relationships that can be verified.

### 1.1 Core decisions

- **Corpus:** all eligible 2023 main research papers in the explicit flagship AI/related venue registry: **34 series, 31 planned in-year editions** (Section 3). NeurIPS/ICML are the historical pilot, not the release boundary. [S1–S3, S20–S29]
- **NLP:** scientific header extraction, affiliation linking and multilabel topic classification.
- **Analysis:** separate researcher, organization and citation projections.
- **Team:** two people, with shared annotation and reciprocal review.
- **Schedule:** re-estimate person-hours and dates for the expanded scope; the old two-venue eight-week baseline is not a validated delivery promise.
- **Priority:** correct entities, paper-specific affiliations and traceable edges.

| Requirement | Implementation decision | Evidence required at submission |
| --- | --- | --- |
| At least 2,000 nodes | Meet the original threshold; additionally target at least 2,000 distinct resolved Researcher nodes | Counts by entity label after deduplication; technical and unresolved records excluded |
| At least 5,000 edges | Require at least 5,000 unique accepted factual edges before adding derived projections | Counts by relation, with factual, taxonomy, and derived totals separated |
| Ten relationship types | Implement the ten semantic predicates in Section 5 | Nonempty relation inventory, definitions, examples, and validation results |
| Accuracy above 90 percent | Propose end-to-end edge precision as the primary operational definition | Frozen random audit, per-type audit, uncertainty intervals, and separate recall measurements |
| Graph DBMS | Neo4j Community with compatible Graph Data Science library | Rebuild instructions, schema, import scripts, saved analysis queries |
| NLP-based construction | Scientific header parsing, affiliation normalization and linking, and controlled multilabel topic classification | NLP inputs, outputs, evidence spans, baseline comparison, and held-out evaluation |
| Report of at least ten pages | Plan a substantive 16–18 page report, excluding cover and optional appendices | Required course sections, figures, evaluation, limitations, and repository URL |

### 1.2 Quality gates

- **Size:** at least 2,000 resolved researchers and 5,000 unique accepted factual edges. The researcher target is stronger than the assignment's total-node minimum.
- **Schema:** all ten relation types present; count factual, inferred, curated and derived edges separately.
- **Precision:** global estimate at least 95%, with the lower bound of a two-sided 95% Wilson interval above 90%.
- **Integrity:** no duplicate semantic edges, invalid endpoints, forbidden self-loops or missing evidence references.
- **Coverage:** target 95% abstract availability and 80% author–paper affiliation resolution; verify these in the pilot.
- **Topics:** target 95% label precision and coverage of at least 80% of eligible papers; also report recall and F1.
- **Rebuild:** reproduce the graph and principal tables from versioned inputs.

**Confirm with the lecturer in week one:** acceptance of a heterogeneous academic network, the meaning of “accuracy”, and whether derived relations and the topic hierarchy count toward the ten predicates.

### 1.3 Scope for two people

| Tier | Included work | When to use it |
| --- | --- | --- |
| Historical pilot | Existing 100-paper NeurIPS/ICML pilot; preserve its data, configs and splits | Diagnostic baseline only; it does not measure expanded coverage |
| Expanded diagnostics | After future collection authorization, add 10 papers per new active venue; 390 cumulative diagnostics if all 29 additions qualify | Check source layouts, missingness, resolution, runtime/storage and review effort per venue |
| Core release | Complete qualifying 2023 main research editions across the 34-series registry; 31 planned editions, with no-edition and access states recorded | Expanded project target; adapters and acquisition are not yet implemented for the new venues |
| Temporal extension | Complete 2022 and 2024 editions using the same inclusion rules | Only after core quality, annotation, and analysis are complete |
| Optional research extension | Collaboration opportunity ranking or an evaluation of temporal link prediction | Only if time remains; not necessary for a strong course project |

- Complete the core release before adding more years, link prediction or advanced models.
- Keep the full official roster; record missing data and justified exclusions.
- Use structured metadata first and parse PDFs selectively.
- Preserve the legacy pilot and measure new venue-specific diagnostics before a future full run.
- Retire the original two-venue paper/researcher/organization sizing estimates for expanded planning. No expanded corpus count or quality score has been measured.
- Re-estimate memory, disk, API/PDF access and reviewer-hours budgets from venue-specific diagnostics; the old 16 GB suggestion is not a full-scope benchmark.
- Do not start discovery, enrichment, PDF downloads, new split creation or graph imports under this planning revision. A later collection instruction is required.
- If a gate fails, fix the cause or disclose the shortfall. Do not lower thresholds after seeing test errors.

## 2 Business purpose and research questions

Use the network to support **research partner scouting, expert discovery and literature prioritization**.

| Question | Relevant graph | Analysis and expected output | Decision supported |
| --- | --- | --- | --- |
| Which researchers connect otherwise separate communities? | Researcher collaboration graph | Weighted degree, approximate betweenness, community membership, supporting papers | Expert discovery and collaboration outreach shortlist |
| Which organizations collaborate across academia and industry? | Organization collaboration graph | Sector mixing, collaboration intensity, bridges, observed international links | Research partnership scouting |
| What AI topics are represented in each organization? | Paper–topic and organization–topic graph | Fractionally counted topic portfolios and diversity | Partner comparison and capability mapping |
| Which papers are influential within the selected corpus? | Directed paper citation graph | Internal in-degree, PageRank, citation communities, age/boundary caveats | Literature prioritization |
| Do collaboration communities align with research topics? | Collaboration graph joined to topic labels | Community topic distributions, entropy, interpretable examples | Identify specialist and interdisciplinary clusters |
| Which findings survive stricter quality filters? | Versioned projections | Rank overlap, rank correlation, component and community changes | Assess confidence in business conclusions |

### 2.1 Rules for business conclusions

- Define influence **within the selected corpus**.
- Describe expertise as evidence from the selected publications.
- Interpret country links as observed organization locations, not researcher nationality.
- Do not equate publication participation with commercial readiness, current employment or employee performance.

### 2.2 Required outputs

- Three evidence-backed business findings.
- Two investigation shortlists with explicit selection criteria.
- For each finding: statistic, denominator, two supporting papers and a material limitation.

## 3 Corpus boundary and source strategy

### 3.0 Flagship conference registry and year policy

The user requested coverage beyond the course examples. Use this explicit,
versioned roster of major international AI and directly related flagship venues.
Specialized flagships remain relevant even when smaller than NeurIPS. This is a
curated scope, not a universal ranking, a verified CORE classification, or all of
computer science. Do not select authors/papers by fame, citations or desired results.

| Area | Conference series | Planned 2023 editions |
| --- | --- | ---: |
| General AI, machine learning and systems | NeurIPS, ICML, ICLR, AAAI, IJCAI, MLSys | 6 |
| Vision, multimedia and medical imaging | CVPR, ICCV, ECCV, ACM Multimedia, MICCAI | 4 |
| Natural language processing | ACL, EMNLP, NAACL, EACL, COLING | 3 |
| Data mining, web, retrieval and recommendation | KDD, The Web Conference (WWW), SIGIR, WSDM, RecSys, CIKM, ICDM, SDM | 8 |
| Statistical learning, uncertainty and theory | AISTATS, UAI, COLT | 3 |
| Robotics and embodied learning | ICRA, IROS, Robotics: Science and Systems (RSS), Conference on Robot Learning (CoRL) | 4 |
| Agents, reasoning and planning | AAMAS, KR, ICAPS | 3 |

- **Year:** retain 2023. ECCV, NAACL and COLING have no 2023 edition; keep no-edition records and do not silently substitute 2022/2024.
- **Readiness:** the other 31 editions are planned candidates. Verify exact official edition IDs, tracks, metadata routes and rights before any future acquisition. No expanded rosters have been collected.
- **Coverage:** include complete qualifying main archival research-paper tracks, including full/short research papers where applicable. Corpus eligibility does not depend on the topic classifier accepting a label.
- **Track mapping:** ACL-family Findings, workshops, demos and nonresearch industry/student tracks are excluded; KDD starts with Research Track only, excluding Applied Data Science; NeurIPS Datasets and Benchmarks stays excluded. Exclude poster-only abstracts, tutorials, invited talks, doctoral consortia, editorials and withdrawn/rejected material.
- **Provenance:** catalog links below are source leads, not verified edition manifests. Preserve unavailable, unknown-track and excluded states; never silently omit venues and claim completeness.
- **Deduplication:** verify cross-venue work/version identity before merging. Retain provider/source crosswalks and the one-primary-Venue schema invariant; unresolved duplicates stay in review.
- **Implementation:** the repository's `configs/conference-scope.yaml` is planning-only with collection disabled. Existing `configs/corpus.yaml`, frozen inputs and the Neo4j graph remain the historical two-venue pilot. Adapters, venue labels, IDs, year windows and split quotas need generalization before an expanded executable config.

### 3.1 Corpus boundary

- **Include:** final, accepted main-conference papers with stable official proceedings records.
- **Exclude:** workshops, tutorials, invited talks, editorials, rejected/withdrawn submissions and supplementary files counted as separate papers.
- **NeurIPS:** explicitly exclude Datasets and Benchmarks from the initial main-track scope. These papers can appear in the same proceedings. [S1, S2]
- **Versions:** represent a preprint and its proceedings version as one deduplicated work when the match is verified.
- **Missing data:** retain the official paper in the corpus ledger even when enrichment or PDF parsing fails.
- **Denominator:** reconcile every included, excluded, failed and unresolved record against the official roster.

### 3.2 Citation boundary

- Core citation analysis uses **core paper → core paper** edges.
- Keep external reference metadata and unresolved targets in staging.
- Optionally add a one-hop cited-paper context layer with `is_core=false`.
- Do not recursively expand external authors, affiliations or references.
- Report core-only and context results separately; context cannot rescue the minimum-size requirement.

### 3.3 Source roles

| Source | What to obtain | Role and limitations |
| --- | --- | --- |
| NeurIPS official proceedings | Paper list, track, title, ordered authors, abstract, PDF URL, proceedings identifier | Primary scope authority; retain track information and official versions [S1, S2] |
| PMLR / MLSys official proceedings | ICML, AISTATS, UAI, COLT, CoRL and MLSys edition records | Verify each edition/volume; the existing ICML pilot uses PMLR 202 [S3, S29] |
| CVF / ECVA | CVPR, ICCV and in-year ECCV official paper records | Distinguish main papers from colocated workshops; ECCV has no 2023 edition [S21] |
| ACL Anthology | ACL, EMNLP, EACL and in-year NAACL/COLING main long/short papers | Findings, demos and workshops are different tracks; verify event/year identifiers [S22] |
| AAAI / IJCAI / dedicated proceedings | AAAI, IJCAI, ICAPS, KR, AAMAS and RSS | Map official research tracks and preserve independent source evidence [S23, S24, S28] |
| ACM / IEEE / SIAM / Springer | Data/web/retrieval/recommendation, ICRA/IROS, multimedia and MICCAI | Use lawful official metadata and permitted full texts; never bypass access restrictions [S25–S27] |
| OpenAlex | Matched work IDs, authorship-specific affiliation strings and institutions, identifiers, outgoing references | Enrichment and reconciliation; neither author IDs nor institution matches are automatically ground truth [S5, S6] |
| Official paper PDF | Printed author–affiliation mapping, organization strings, abstract, references | Primary evidence for paper-time affiliations and disputed mappings; parse with GROBID [S10] |
| OpenReview public records | Public author identifiers, paper links, keywords, appropriate public profile information | Secondary identity evidence; profile current affiliation must not become a historical paper affiliation [S9] |
| ROR | Organization identifiers, names, aliases, organization metadata | Canonicalization aid; no-match and ambiguous-match cases require review [S11] |
| Wikipedia and organization websites | Optional descriptions and manually checked aliases | Enrichment only; not necessary for the core graph or its minimum size |

### 3.4 Claim-specific precedence

- **Acceptance and byline:** official proceedings.
- **Paper-time affiliations:** the published author–affiliation block or aligned authorship-specific metadata.
- **Identity:** verified identifiers plus compatible paper evidence.
- **Citation:** explicit reference evidence and a verified target.
- Keep conflicting claims and the resolution decision; copied websites are not independent confirmations.

### 3.5 Access and collection limits

- No Google Scholar scraping dependency or paid service is required.
- Current OpenAlex guidance checked for this plan supports casual keyless queries, a free verified key for scale, and key-based cursor paging beyond the first page. [S7, S8]
- Cache responses, monitor allowance use and respect current request limits.
- Record retrieval date, source URL, content hash and available license information.
- Keep credentials outside Git; distribute permitted metadata and acquisition instructions for restricted inputs.

## 4 System architecture and data contracts

**Keep raw inputs immutable.** Candidate records pass through validation before they enter the accepted graph.

| Stage | Input | Processing | Durable output and gate |
| --- | --- | --- | --- |
| Discover | Official conference indexes | Enumerate eligible papers and tracks | `corpus_manifest.parquet`; counts reconcile with roster |
| Acquire | Manifest and source identifiers | Fetch metadata, resolve work records, download needed PDFs | Raw JSON/HTML/PDF plus retrieval log and content hashes |
| Extract | Raw records and PDFs | Parse headers and references; normalize text | `paper_records`, `author_mentions`, `affiliation_mentions`, `reference_mentions` |
| Resolve | Mentions and external identifiers | Deduplicate papers, resolve authors and organizations, align affiliations | Canonical entity tables, crosswalks, review queue, resolution history |
| Enrich | Abstracts and controlled vocabulary | NLP topic assignment with evidence and abstention | `paper_topics` and model/threshold metadata |
| Validate | Candidate nodes and relations | Schema, evidence, confidence, duplication, temporal checks | Accepted tables, rejection reasons, quality report |
| Construct | Accepted facts | Load factual relations, then compute derived relations | Versioned Neo4j graph and reproducible relation tables |
| Analyze | Named projections | EDA, SNA, sensitivity checks, business cases | Metrics tables, figures, query outputs, dashboard |

### 4.1 Canonical data contracts

- **Papers:** stable ID, official URL, title, abstract, venue, year, track, verified external IDs and core/context status.
- **Researchers:** stable internal ID, display name, aliases, external identifiers and resolution status.
- **Organizations:** stable ID, canonical name, aliases, sector, location metadata and normalization decisions.
- **Authorships:** researcher ID, paper ID, byline position, raw mention and evidence reference.
- **Author–paper affiliations:** researcher ID, paper ID, organization ID, raw affiliation and marker/alignment evidence.
- **Paper topics:** paper/topic IDs, supporting text, method, score, decision band and model/taxonomy versions.
- **Citations:** citing/cited IDs, reference locator, target-match evidence and boundary status.
- **Edge evidence:** edge ID, support-record IDs, exact source locator, validation status and version.

**The affiliation triple is mandatory.** It records which paper supports each person's organizational connection.

### 4.2 Provenance required on every accepted edge

- Relation type, semantic endpoints and deterministic `edge_id`.
- Evidence kind: `observed`, `inferred_topic`, `derived` or `curated_taxonomy`.
- Resolvable evidence IDs, method version, graph version and validation status.
- Source URL/record ID, retrieval timestamp and raw-file SHA-256.
- Source-field path or PDF page/TEI locator; a minimal permitted supporting excerpt.
- Derived edges: exact input edges and distinct supporting papers.

### 4.3 Storage rules

- Store the full evidence ledger in Parquet/JSONL and reference it from Neo4j.
- Avoid enormous support arrays on high-degree edges.
- Keep uncertain records in a review queue.
- Never compare unrelated rule/model scores as interchangeable probabilities.

## 5 Graph schema and the ten relationships

### 5.1 Node meanings

| Label | Meaning | Identifier and required properties |
| --- | --- | --- |
| Researcher | One resolved person, not one occurrence of a name | Stable internal ID, display name, resolution status, identity evidence |
| Organization | One defined research institution or corporate research entity | Stable internal ID, canonical name, sector, normalization policy, optional ROR ID |
| Paper | One deduplicated research work represented by its selected proceedings version | Stable internal ID, title, year, official URL, track, `is_core` |
| Topic | One concept in a frozen project taxonomy | Stable taxonomy ID, label, definition, level, version |
| Venue | A conference series in the expanded flagship registry | Stable series ID and name; edition year is stored on Paper |

- Keep year and country as properties unless a justified analysis needs separate nodes.
- Do not count raw files, API responses, indexes, evidence records or unresolved placeholders as domain nodes.

### 5.2 Ten relationship types

| ID and predicate | Endpoints | Meaning and minimum evidence |
| --- | --- | --- |
| R1 AUTHORED | Researcher → Paper | The resolved researcher appears on the official paper byline; retain author order |
| R2 AFFILIATED_WITH | Researcher → Organization | At least one accepted author–paper–organization observation supports this paper-time affiliation |
| R3 PUBLISHED_IN | Paper → Venue | The official proceedings list this paper in the selected venue and year |
| R4 CITES | Paper → Paper | An explicit reference from the citing work resolves to the target work |
| R5 HAS_TOPIC | Paper → Topic | Title/abstract analysis supports a leaf topic under the frozen annotation rules |
| R6 SUBTOPIC_OF | Topic → Topic | A manually defined leaf belongs to a parent in the project taxonomy |
| R7 COAUTHORED_WITH | Researcher ↔ Researcher | Two distinct resolved researchers share at least one accepted core paper |
| R8 COLLABORATED_WITH | Organization ↔ Organization | A shared core paper contains two distinct authors with supported affiliations to the two distinct organizations |
| R9 RESEARCHES_TOPIC | Researcher → Topic | At least two distinct accepted core papers authored by the researcher have that leaf topic |
| R10 CONTRIBUTES_TO_TOPIC | Organization → Topic | At least three distinct accepted core papers connect the organization to that leaf topic through paper-specific affiliations |

- **R1–R4:** observed factual relations.
- **R5:** NLP-inferred topic labels.
- **R6:** manually curated taxonomy.
- **R7–R10:** derived collaboration/profile summaries, not independent extraction tasks.
- Reverse copies do not create new relationship types.

### 5.3 Edge keys and derivation rules

#### AUTHORED

- Unique key: `(researcher_id, paper_id)`.
- Match a resolved identity to the official byline and preserve author order.
- Keep unresolved mentions in staging until a defensible person identity is available.

#### AFFILIATED_WITH

- Unique graph key: `(researcher_id, organization_id)`.
- Aggregate accepted author–paper–organization observations and retain observed years.
- Filter by year through the canonical triple table.
- An observed year does not establish employment start, duration, type or current employer.

#### PUBLISHED_IN

- Unique key: `(paper_id, venue_id)`; exactly one primary series per core paper.
- Retain the edition year on Paper.
- Preprint availability does not prove conference acceptance.

#### CITES

- Unique key: `(citing_paper_id, cited_paper_id)` after work deduplication.
- Multiple confirmations are evidence for one edge.
- Direction: citing → cited; author overlap does not invalidate the reference.
- Reject self-loops caused by matching alternate versions of the same work.

#### HAS_TOPIC

- Unique key: `(paper_id, leaf_topic_id)`.
- Accept one to three supported leaf labels, or abstain.
- Retain a supporting text span or explicit decision explanation.
- A passing related-work mention does not establish the paper's topic.

#### SUBTOPIC_OF

- Unique key: `(leaf_topic_id, parent_topic_id)`.
- Freeze the project taxonomy and audit every hierarchy edge.
- Reject cycles; do not generate topics to inflate graph size.

#### COAUTHORED_WITH

- Store one canonical pair orientation; analyze as undirected.
- Count distinct supporting core papers.
- A paper with `k > 1` authors contributes `1 / (k - 1)` to each author pair.
- Retain both raw shared-paper count and fractional weight.

#### COLLABORATED_WITH

- Require two distinct organizations and two distinct authors on the same paper.
- Each author must have an accepted affiliation observation supporting the relevant organization.
- A sole dual-affiliated author does not create the relationship.
- Store one canonical pair; deduplicate support by paper.
- If a paper has `q > 0` eligible organization pairs, add `1 / q` to each pair.

#### RESEARCHES_TOPIC

- Require at least **two distinct accepted core papers** by the researcher with that leaf topic.
- Count works, not duplicate labels or alternate versions.
- A one-paper contribution remains visible through AUTHORED and HAS_TOPIC.

#### CONTRIBUTES_TO_TOPIC

- Require at least **three distinct accepted core papers** with the leaf topic.
- Support the organization through affiliations on those exact papers.
- Publication participation does not establish ownership, funding or commercial capability.

**Unsupported predicates:** do not add supervision, employment, funding or method-use claims without explicit evidence and a separate annotation policy.

### 5.4 Worked example

**Invented example, not collected data.** Each paper is at ICML 2023 and has the NLP/language-model topic.

| Paper | Printed author affiliations | Additional observation |
| --- | --- | --- |
| P1 | Researcher A at Organization X; Researcher B at Organization Y | No additional citation in this example |
| P2 | Researcher A at Organization X; Researcher C at Organization Y | Cites P1 |
| P3 | Researcher D at Organization X; Researcher E at Organization Z | Cites P1 |

- A–B, A–C and D–E become coauthor pairs.
- X–Y has two supporting papers; X–Z has one.
- Researcher A passes the two-paper RESEARCHES_TOPIC rule.
- Organization X passes the three-paper CONTRIBUTES_TO_TOPIC rule; Y and Z do not.
- No observation establishes current employment.

## 6 Collection specification

### 6.1 Discover the official corpus

1. After collection is separately authorized, verify every in-year registry entry, official edition source, accepted research track and exclusions. Record no-edition and unavailable states; do not silently substitute sources/years. [S1–S3, S20–S29]
2. Enumerate every official paper; retain the original responses and parser version.
3. Extract stable ID, title, ordered authors, abstract, year, track and source/PDF links.
4. Inspect at least ten records per venue across index positions and layouts.
5. Reconcile included, excluded, failed, unavailable and pending records; verify cross-venue duplicate/version groups and freeze the new manifest hash. Preserve old frozen manifests and reserve supplemental held-out groups before enrichment.

### 6.2 Match external work records

- Prefer a verified DOI or linked identifier; a DOI is optional.
- Otherwise combine title, year, venue and author evidence.
- Never accept title similarity alone.
- Retain candidate scores, rejected alternatives and review decisions.
- Keep the official paper if enrichment fails.
- Reconcile full bylines; retrieve individual work records when list results truncate authorships. [S5]

### 6.3 Extract paper evidence

- Use GROBID `processHeaderDocument` for authors, affiliations, abstract and available links.
- Use `processFulltextDocument` for references, document structure or disputed mappings.
- Verify author markers against PDFs during the pilot.
- Disable or document external consolidation. [S10]
- Retain page/TEI locators; never infer affiliation assignment from page-text order alone.
- Bound retries and route unresolved cases to review; preserve other valid edges.

### 6.4 Make collection resumable

- Use source-specific concurrency, timeouts, backoff with jitter and bounded retries.
- Honor retry timing and stop at usage limits.
- Cache by canonical ID and content hash; resume successful records.
- Log source, URL, time, status, attempts, raw path, hash, parser version and final state.
- Distinguish missing source fields, access restrictions, parse failures and ambiguous matches.

### 6.5 Pilot exit checklist

- Measure throughput, median PDF size, parsing time and API use.
- Measure abstract coverage, work-match rate and affiliation-triple resolution.
- Measure review minutes per difficult case for the two-person workload.
- Estimate source-family-specific full-run costs from new diagnostics; do not multiply the two-venue pilot throughput across every publisher.
- Validate edition-qualified IDs, venue names, year windows and staged quotas; listing venues does not implement a collector.
- Revisit taxonomy definitions for medical imaging, robotics, retrieval, systems and symbolic reasoning using development evidence before freezing labels.
- Fix systemic parser/matching defects before scaling.
- Avoid selecting only famous authors, highly cited works or easy PDFs.

## 7 Preprocessing and entity resolution

### 7.1 Text cleaning

- Preserve raw and normalized fields side by side.
- Normalize Unicode, whitespace, HTML entities and cautious PDF line-break hyphenation.
- Preserve proper names, mathematics and technical tokens such as LLM, GNN and OOD.
- Flag short/missing abstracts, navigation text, encoding failures and title mismatches.
- Flag unexpected languages instead of using an untested NLP model.
- Use separate cleaning policies for names, organizations and semantic text.

### 7.2 Paper identity

- Use an internal ID anchored to the official proceedings record.
- Maintain crosswalks to DOI, OpenAlex and OpenReview IDs.
- Merge versions only with corroborating identifiers or title/byline evidence.
- Display the proceedings version and retain aliases.
- Resolve citations to the deduplicated work ID.

### 7.3 Researcher identity

| Case | Decision |
| --- | --- |
| Same verified ORCID and compatible paper evidence | Strong merge candidate; check contradictions |
| Same public profile identifier linked from the paper record | Strong identity signal; verify byline alignment |
| Same name with overlapping coauthors and compatible affiliations | Candidate for calibrated resolution or review |
| Same common name with inconsistent coauthor or organization context | Keep separate pending additional evidence |
| Initial-only name or name-order variation | Resolve using additional evidence; never expand an initial by guessing |
| Two presumed identities occur separately on the same byline | Block their merge unless a documented source correction exists |

- Keep internal IDs stable when external providers recluster authors.
- Use names, affiliations, coauthors and topics to generate candidates, not to prove identity on their own.
- Never merge on normalized name alone.
- Keep mention-to-person decisions reversible and auditable.
- Measure false merges and false splits; inspect common-name hubs.
- Disclose provisional/unresolved identities and exclude anonymous placeholders from the researcher target.

### 7.4 Organization identity

- Retain raw names and an approved alias table.
- Check candidate ROR/external IDs against name, location and hierarchy.
- For ROR matching, prefer the documented `chosen` indicator over the largest numeric score; review ambiguities. [S11]
- Default to university/independent institution or the paper-supported corporate research entity.
- Keep labs/departments as attributes unless separately justified.
- Distinguish independent campuses, hospitals and joint institutes consistently.
- Preserve historical names; make current-parent aggregation a separate documented view.
- Headquarters location does not establish every author's work location.

### 7.5 Author-specific affiliation alignment

- Accept explicit authorship-level metadata or verified PDF markers.
- Store `(author, paper, organization)` observations before aggregation.
- Do not assign every listed organization to every author.
- If mapping is ambiguous, preserve mentions and withhold unsupported edges.
- Missing affiliation means **unknown**, not independent researcher.
- Missing sector means **unknown**, not university.
- Check missingness by venue, team size and sector.

## 8 NLP methodology and topic specification

### 8.1 Required NLP components

- Scientific header entity extraction with GROBID.
- Affiliation-string normalization and organization linking.
- Multilabel topic assignment from titles and abstracts.
- Structured metadata corroborates outputs; CSV/API ingestion alone is insufficient.
- Separate extraction quality from author–affiliation linking quality. [S12]

### 8.2 Controlled taxonomy

| Parent group | Leaf topics |
| --- | --- |
| Language and perception | Natural language processing and language models; Computer vision; Multimodal learning; Information retrieval and recommendation |
| Learning and representation | Generative modeling; Graph machine learning; Representation learning; Probabilistic and Bayesian learning |
| Decision and interaction | Reinforcement learning; Robotics and embodied AI; Multi-agent systems; Planning and reasoning |
| Reliability theory and systems | Trustworthy machine learning; Optimization and learning theory; Efficient machine learning systems; Causal inference |

- Freeze the 16 proposed leaves and four parent groups after the pilot.
- Give each leaf a definition, synonyms, inclusions, exclusions and confusing examples.
- Permit overlapping labels; parent groups organize the project vocabulary.
- Label the substantive problem/method, not every term mentioned.
- Example: graph-based recommendation can support both Graph ML and Retrieval/recommendation.
- Define subthemes within Trustworthy ML without generating unsupported extra labels.

### 8.3 Baseline and accepted model

- **Baseline:** versioned phrase dictionary with exclusions and ambiguous-token rules.
- **Recommended:** title/abstract embeddings compared with topic definitions and labeled examples.
- **Optional:** a small multilabel classifier on frozen embeddings, if additional training labels are feasible.
- Candidate tools include Sentence Transformers and scientific-document models such as SPECTER. [S13, S14]
- Calibrate thresholds by label on development data; cosine similarity is not a probability.
- Require supporting text and retain method/model versions.
- Route uncertain cases to review or abstain.

### 8.4 Optional LLM assistance

- Restrict labels to the frozen taxonomy and the supplied title/abstract.
- Require structured outputs and verify quoted spans programmatically.
- Evaluate independently; one model cannot be the sole annotator and sole judge.
- No paid LLM or custom general-purpose NER training is required.

### 8.5 Gold labels and held-out testing

- **Historical development:** preserve the existing 60 NeurIPS/ICML paper IDs (30 per venue), including all existing exposure/tuning records.
- **Historical held-out test:** preserve the existing 120 NeurIPS/ICML IDs (60 per venue); all their cross-venue versions also remain excluded from development.
- **Expanded allocation:** before future acquisition/tuning, freeze supplemental venue-stratified leakage groups. Keeping the current per-venue defaults for 31 editions would mean **1,860 test / 930 development papers**. These are arithmetic workload scenarios, not new frozen samples. Finalize a feasible allocation and two-reviewer hours budget prospectively; no quality gates are reduced.
- **Staged diagnostics:** plan 10 papers from development/pool groups per newly active venue (390 cumulative with the legacy pilot if all additions qualify). Difficult-layout diagnostics and unequal pilot quotas are not a population accuracy estimator.
- Reserve test IDs before pilot tuning; exclude all versions from training and development.
- If supervised training is used, create a separate additional training set.
- Both teammates annotate test papers independently, then adjudicate disagreements.
- Annotate entities, author-specific affiliations, complete topic labels and references to in-core targets.
- Add same-name negatives and name-variant positives for identity evaluation.
- Report per-venue/source-family metrics and sampling weights for corpus-wide TP/FP/FN totals. The legacy 60/60 test cannot represent the expanded population; disclose tiny-stratum uncertainty and quarantine later-discovered leakage.
- Report rare-topic diagnostic sets separately, with label support and agreement.
- Tune only on development data; use a fresh untouched test after model changes.
- Separate automated-pipeline results from manually corrected release quality.

### 8.6 Topic portfolio counting

- A paper with `L` accepted labels contributes `1 / L` to each label.
- Optional fractional author output uses `1 / k` for `k` resolved authors.
- Organization portfolios use `1 / m` across supported organizations, then `1 / L` across labels.
- Keep raw distinct-paper counts for R9/R10 thresholds.
- Display abstentions and unknown coverage; do not invent a topic node for missing labels.

## 9 Graph construction and structural quality

### 9.1 Build sequence

1. Freeze canonical entities and accepted support facts.
2. Load the five node labels with uniqueness constraints.
3. Load R1–R5 and the curated R6 taxonomy.
4. Recompute R7–R10 from accepted **core, paper-specific** support only.
5. Validate keys, types, evidence, support counts and orientation.
6. Reconcile Neo4j counts with canonical tables.
7. Freeze the graph version and create named analysis projections.

- Deterministic edge ID: relation type plus semantic endpoint IDs.
- Two source confirmations remain one semantic edge.
- Retain taxonomy version and derivation thresholds.
- Reimporting unchanged inputs must not increase counts.

### 9.2 Structural checks

| Check | Expected result or response |
| --- | --- |
| Node identifier uniqueness | Zero duplicates per label |
| Endpoint schema | Every relation matches the endpoint types in Section 5 |
| Core paper invariants | Exactly one primary venue; at least one accepted author or an explicit unresolved-author exception |
| Citation and social self-loops | Zero invalid loops; investigate version-matching errors |
| Symmetric storage | One canonical edge per person pair or organization pair |
| Derived edge support | Recomputed support count equals distinct supporting core papers |
| Topic hierarchy | No cycles; all leaves connected to their approved parent |
| Evidence completeness | Every accepted edge has resolvable provenance |
| Affiliation contamination | No graph edge created from an unaligned paper-level institution list |
| Isolates and large hubs | Investigate; do not delete legitimate isolates or assume hubs are errors |
| Repeated import | Counts, edge keys, and metric inputs remain identical |

- Inspect the 20 largest researcher hubs and organization collaboration supports.
- Investigate legitimate consortium cliques as well as false merges and affiliation-product errors.
- Keep legitimate isolates; connectedness alone is not quality.

### 9.3 Analysis projections

| Projection | Nodes and edges | Intended interpretation |
| --- | --- | --- |
| Researcher collaboration | Core researchers and undirected COAUTHORED_WITH | Observed co-publication relationships |
| Organization collaboration | Supported organizations and undirected COLLABORATED_WITH | Observed joint-paper collaboration under the distinct-author rule |
| Core citations | Core papers and directed CITES, core to core only | Influence and knowledge flow within the selected proceedings boundary |
| Paper topic bipartite | Core papers, leaf topics, HAS_TOPIC | Research-area composition without social-edge assumptions |
| Organization topic bipartite | Organizations, leaf topics, CONTRIBUTES_TO_TOPIC plus portfolio weights | Evidence-supported publication portfolios |

**Centrality rule:** do not mix people, venues, topics and organizations in one global PageRank and call it researcher influence.

## 10 Accuracy measurement and quality assurance

### 10.1 Define what accuracy means

- Proposed primary metric: **end-to-end edge precision**.
- An edge passes only if endpoints, predicate, paper/time scope and evidence are all correct.
- Wrong identities, unsupported affiliations and duplicate semantic claims fail the audit.
- `Precision = TP / (TP + FP)`.
- `Recall = TP / (TP + FN)`; `F1 = 2PR / (P + R)`.
- Measure recall on fully annotated held-out papers; a complete real-world reference graph is unavailable.
- Do not compute “accuracy” over all possible node pairs: trivial nonedges dominate.

### 10.2 Three complementary checks

- **Global audit:** freeze the graph and draw 600 unique edges uniformly without replacement, with a recorded seed.
- **Per-type audit:** draw 100 edges per predicate, or audit the whole population if it is smaller.
- **Targeted review:** inspect ambiguous identities, top hubs, largest teams, institutional rollups and bridge nodes.
- Both teammates review independently, then adjudicate.
- Count unverifiable evidence as a failed release edge.
- Reuse overlapping reviews, but retain separate sampling flags.
- Never pool supplemental type samples into an unweighted global score.
- Targeted findings discover errors; they do not estimate random-sample precision.

### 10.3 Release thresholds

- Global precision point estimate **≥95%**.
- Lower bound of a two-sided **95% Wilson interval >90%**.
- Report correct count, sample size, estimate and interval.
- Worked example: **570/600 → 95.0%**, with lower bound **≈92.95%**.
- A relation with **96/100** has lower bound **≈90.16%**; **95/100** has only **≈88.83%**.
- These are planning examples, not measured project results.
- Small populations: report exact census correctness.
- Per-type intervals are individual, not a simultaneous 95% guarantee across all ten types.
- If a simultaneous claim is required, predefine multiplicity adjustment and sample sizes.

### 10.4 Pipeline metrics

| Component | Evaluation unit and metric | Practical goal |
| --- | --- | --- |
| Header entities | Exact-span and normalized entity precision, recall, F1 on held-out PDFs | Identify extraction errors separately from linking errors |
| Researcher resolution | Pairwise precision/recall/F1 plus cluster-level error analysis | Target pairwise precision at least 98 percent; report hard-name cases |
| Organization resolution | Correct canonical organization per annotated affiliation mention | Target at least 95 percent precision with coverage reported |
| Author affiliation alignment | Correct author–paper–organization triples | Target at least 95 percent precision; disclose unresolved proportion |
| Topic assignment | Label micro/macro precision, recall, F1 and per-label support | Target at least 95 percent precision and 80 percent paper coverage; do not rename precision as accuracy |
| Citation resolution | Correct target among annotated in-core references; precision and recall | Target at least 98 percent precision; report unmatched references |
| Derived relations | Source validity plus exact recomputation of support and weight | No derivation mismatch; audit semantic correctness as well |
| Topology stability | Top-k overlap, rank correlation, component/community changes | Conclusions robust enough to disclose their sensitivity |

- Publish macro/per-type precision alongside the uniform global estimate.
- Report recall, F1, abstentions and unresolved coverage.
- Audit semantic support for derived edges, not just successful joins.
- Shared upstream evidence means derived edges are not independent extraction tasks.
- If the lecturer requires NLP F1 above 90%, make that a separate week-one acceptance gate.

### 10.5 Correction protocol

1. Record issue, competing entities, evidence, reviewer decisions and timestamp.
2. Fix the underlying rule where possible.
3. Regenerate dependent edges and rerun integrity checks.
4. Version the corrected graph.
5. Retain the original frozen audit result; use a fresh blind sample for a new independent release claim.

**Error categories:** false merge/split, wrong organization, wrong author-affiliation link, wrong topic, duplicate version and wrong citation target.

## 11 Exploratory data analysis

### 11.1 Before graph construction

| Analysis | Measurement or figure | Why it matters |
| --- | --- | --- |
| Corpus composition | Included/excluded/pending papers by venue, year, and track | Establishes the boundary and catches wrong-track ingestion |
| Field completeness | Missingness table for abstracts, IDs, affiliations, countries, and references | Quantifies what the pipeline can and cannot know |
| Source matching | Work-match and disagreement rates by venue | Finds systematic enrichment errors |
| Team sizes | Author-count histogram and extreme cases | Exposes truncated lists and consortium effects |
| Identity ambiguity | Mentions per person, same-name clusters, review outcomes | Diagnoses false merges and splits |
| Affiliation structure | Organizations per author–paper and papers with unaligned affiliations | Detects Cartesian-product mistakes and multi-affiliation complexity |
| Text characteristics | Abstract length, encoding failures, language flags | Tests NLP input quality |
| Topics | Label frequencies, multilabel counts, confidence bands, abstentions | Finds dominant labels and poorly calibrated classes |
| References | Reference counts, in-core resolution rate, unresolved-target reasons | Establishes citation coverage and boundary effects |

- Compare missingness by venue and team-size band, not only globally.
- Keep unknown sector/country values in denominators.
- Check whether enrichment failures systematically remove particular institutions or layouts.
- Save each plot's underlying table.

### 11.2 After graph construction

- Counts by node and relation type.
- Factual, inferred, curated and derived edge totals.
- Average/median degree and support-weight distributions.
- Components, isolates, clustering and projection-specific density.
- Team-size effects, large hubs, dense organization cliques and unresolved aliases.

### 11.3 Counting conventions

- Undirected simple-graph density: `2m / [n(n-1)]`.
- Directed density without self-loops: `m / [n(n-1)]`.
- State whether isolates are included.
- Use degree histograms or complementary cumulative distributions.
- A straight log plot does not establish a power law.
- Every figure needs a question, denominator, graph version and boundary.

## 12 Social network analysis plan

### 12.1 Required analyses

| Analysis | Projection and method | Interpretation and safeguards |
| --- | --- | --- |
| Collaboration structure | Researcher and organization graphs; components, degree, weighted strength, clustering | Compare raw shared-paper count with fractional weights |
| Researcher bridges | Researcher graph; approximate betweenness and community membership | Use inverse positive strength as distance if weighted shortest paths are intended; disclose approximation and sample size |
| Communities | Weighted collaboration graph; Leiden or Louvain | Record algorithm, seed, resolution, graph version; inspect supporting topics and papers |
| Sector collaboration | Organization graph; sector mixing matrix and university–company shared-paper counts | Unknown sector remains visible; links do not establish formal contracts |
| International structure | Organization graph; observed cross-country links | Use the defined location policy and avoid nationality claims |
| Citation influence | Directed core citation graph; internal in-degree and PageRank | Citing → cited direction; disclose sinks, sparse same-year links, and corpus boundary |
| Topic portfolios | Paper–topic and organization–topic graphs; fractional shares and diversity | Include support counts and topic coverage; compare organizations of similar output where useful |

- Use named projections and a compatible Neo4j GDS version. [S15–S17]
- GDS Community has resource/catalog limits; verify compatibility in the pilot.
- NetworkX can provide independent checks or a documented fallback. [S18]
- For weighted shortest paths, convert positive collaboration strength to distance when appropriate.
- Disclose betweenness approximation settings.
- For communities, record seed and resolution; compare three seeds and at least two resolutions.
- Interpret communities using topics, representative entities and supporting papers.
- If in-core citations are sparse, report that boundary effect; similarity edges are not citations.

### 12.2 Three business case studies

1. **Academic–industry partner map:** one leaf topic, organizations with sufficient support, topic shares and two evidence-backed partnership candidates.
2. **Researcher bridge profile:** source-supported collaboration paths, community context and a checked identity.
3. **Organization comparison:** fractional topic portfolios, paper counts, affiliation coverage and a decision-relevant limitation.

### 12.3 Optional extensions

- A heuristic collaboration shortlist must disclose its criteria and evidence.
- Shared topics do not prove an existing collaboration or future partnership success.
- Analyze trends only after adding complete adjacent years; compare shares as well as counts.
- An observed affiliation change does not necessarily mean a job change.
- For temporal prediction, use earlier features and later complete-edition evaluation.
- Exclude future coauthors, affiliations, topics and citation counts from features.
- Specify candidate pairs, negative sampling, precision at k and coverage.
- For this two-person baseline, defer prediction until collection, quality and reporting are complete.

## 13 Targeted comparisons and robustness checks

Use a few comparisons that directly test whether the graph's conclusions are trustworthy.

| Comparison | Question tested | Minimum evidence |
| --- | --- | --- |
| Name-only matching versus resolved identities | Do naive identity rules create false bridges and hubs? | Audit error rates, top-20 overlap, and two corrected false-merge examples; naive version stays outside the release |
| Keyword baseline versus supported topic classifier | Does NLP improve semantic edges beyond simple keywords? | Held-out precision/recall/F1, label coverage, and confusion examples |
| Accepted release versus stricter evidence filter | Are major findings sensitive to uncertain facts? | Top-20 overlap, Spearman correlation on common nodes, largest-component share, case-study changes |
| Raw versus fractional collaboration weights | Are large teams dominating centrality? | Rank changes and top-hub support sizes |
| Core citations versus separately marked context | How much does the network boundary affect influence? | Node/edge counts, citation coverage, and leading-paper overlap |

### 13.1 Comparison rules

- Freeze stricter evidence filters before reading final conclusions.
- Rebuild derived edges from filtered support records.
- Do not merely remove low-score aggregate edges.
- Compare top-20 overlap, rank correlation on common nodes, component share and case-study changes.
- Keep naive/error-prone baselines outside the release graph.

### 13.2 Report efficiently

- One quality comparison table.
- One robustness table or combined figure panel.
- A few concrete error/correction examples.
- No new figure for every metric.
- Defer GNNs and large prediction benchmarks until all core requirements pass.

## 14 Technology stack and repository specification

### 14.1 Recommended stack

| Layer | Recommended choice | Reason |
| --- | --- | --- |
| Collection and orchestration | Python, HTTP client, BeautifulSoup or lxml, command-line stage runner | Accessible implementation and resumable collection |
| Storage before graph load | Parquet and JSONL; lightweight local metadata ledger | Preserves raw fields, canonical tables, provenance, and repeatable joins |
| Scientific NLP | GROBID service, text normalization, documented embedding/classification model | Structured document extraction plus abstract semantics |
| Quality checks | Schema validation and explicit assertion queries | Makes release criteria executable |
| Graph DBMS | Neo4j Community with Python driver and Cypher | Typed property graph, understandable querying, course-compatible storage |
| Graph algorithms | Compatible Neo4j GDS; NetworkX for checks and documented fallback | Named projections and reproducible algorithms |
| EDA and plots | pandas, matplotlib/seaborn or Plotly | Reproducible statistics and clear figures |
| Demonstration | Streamlit plus a graph component or Neo4j Browser | Adequate course demo without a separate production frontend |
| Environment | Docker Compose, dependency lockfile, example environment configuration | Consistent service and package versions |

- Pin service images, dependencies and model revisions after the pilot.
- Record actual versions; avoid “latest” in the final release.
- Keep the local Neo4j workflow sufficient for submission.
- Use a small Streamlit/Neo4j Browser demonstration; no separate production frontend is required.
- Hosted deployment, authentication and external APIs are optional project extras.

### 14.2 Repository structure

| Path | Responsibility |
| --- | --- |
| `README.md` | Scope, schema summary, quick start, data access, quality results, report and demo links |
| `configs/corpus.yaml` | Venue editions, tracks, input sources, and cutoff policy |
| `configs/quality.yaml` | Calibrated acceptance rules and audit seeds |
| `configs/topics.yaml` | Frozen taxonomy, definitions, synonyms, and version |
| `src/collect/` | Proceedings adapters, API enrichment, PDF retrieval, retry and cache logic |
| `src/preprocess/` | Text cleanup, TEI parsing, mention extraction |
| `src/resolve/` | Paper, person, and organization resolution; review decisions |
| `src/nlp/` | Topic baseline, classifier, evidence checks, evaluation |
| `src/graph/` | Canonical edge generation, validation, Neo4j import, projections |
| `src/analysis/` | Statistics, centrality, communities, business case generation |
| `src/evaluation/` | Gold-set scoring, audit sampling, confidence intervals, error analysis |
| `app/` | Demonstration views and evidence inspection |
| `queries/` | Schema, integrity, audit, and business Cypher queries |
| `tests/fixtures/` | Small synthetic or permitted cases for the highest-risk transformations |
| `data/manifests/` | Versioned source roster and acquisition metadata |
| `data/raw/`, `data/interim/` | Cached sources and processing outputs; exclude restricted or large inputs from Git |
| `data/processed/` | Release-ready canonical entity and relation tables |
| `reports/` | Figure data, quality summaries, final report, and limitations |
| `docs/` | Schema, annotation guide, source policy, data dictionary, and contribution record |

- Expose commands for discover, acquire, extract, resolve, classify, validate, build, analyze and evaluate.
- Accept versioned configuration and input/output paths.
- Exit nonzero on blocking validation failures.
- Resume completed records and write run summaries.
- Replace the repository URL template with the actual URL and release tag before submission.

### 14.3 High-value tests

- Same name, different person; name-order and initial variants.
- One author with two affiliations; distinct authors with distinct organizations.
- A sole dual-affiliated author must not create an organization collaboration.
- Duplicate paper versions and repeated references.
- Topic abstention and unsupported labels.
- Idempotent import and exact derived-support/weight recomputation.

### 14.4 Neo4j schema setup

Verify these illustrative constraints against the pinned Neo4j version. [S19]

```cypher
CREATE CONSTRAINT researcher_id IF NOT EXISTS
FOR (n:Researcher) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT organization_id IF NOT EXISTS
FOR (n:Organization) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT paper_id IF NOT EXISTS
FOR (n:Paper) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT topic_id IF NOT EXISTS
FOR (n:Topic) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT venue_id IF NOT EXISTS
FOR (n:Venue) REQUIRE n.id IS UNIQUE;
```

Also implement queries for counts, duplicate keys, invalid endpoints, missing provenance and support-paper inspection. Constraints alone do not establish semantic correctness.

## 15 Demonstration and visualization specification

### 15.1 Demonstration views

| View | Required behavior |
| --- | --- |
| Overview | Show node/edge counts by type, corpus boundary, quality summary, and known coverage gaps |
| Entity explorer | Search researchers and organizations; distinguish same-name entities; display aliases, paper support, observed affiliations, and source links |
| Network explorer | Choose researcher, organization, or citation projection; filter by topic and sector; inspect bounded neighborhoods |
| Topic and organization comparison | Show fractional portfolio charts, publication support, and coverage denominators |
| Evidence and quality | Inspect a selected relation’s source records, method, review state, and derivation support |

### 15.2 Visual design rules

- Show graph version, corpus boundary and relevant coverage.
- Search must distinguish same-name researchers.
- Keep source evidence one click from the selected edge.
- Distinguish observed, inferred and derived relationships.
- Encode node type with shape/color, a stated metric with size, and stated support with edge thickness.
- Include a legend and paper-time affiliation language.
- Start with neighborhoods of about 100–300 nodes; expand on request.

### 15.3 Compact report figure set

- Collection and quality overview.
- Degree and component distributions in one panel.
- Collaboration communities with topic profiles.
- Organization sector and topic comparison.
- Citation map with the boundary stated.
- Every caption: projection, filter, counting convention and graph version.

## 16 Task allocation and revised workload planning

### 16.1 Two-person ownership

| Person | Primary ownership | Cross-review |
| --- | --- | --- |
| A — Data and graph engineering | Collection, paper/person/organization resolution, affiliation triples, canonical tables, Neo4j, derived edges and reproducible builds | Reviews B's topic decisions, NLP evaluation and analysis queries |
| B — NLP and analysis | Header extraction, topic guide/model, gold-set coordination, EDA, SNA, business cases, demo and report integration | Reviews A's identity decisions, affiliation mapping and graph derivation |

### 16.2 Shared responsibilities

- Both annotate the held-out papers and sampled edges independently.
- Resolve disagreements together and record the decision.
- Neither person is the sole author and sole evaluator of the same extraction rule.
- A writes collection/graph/reproducibility sections; B writes NLP/analysis sections.
- Both check results, limitations, references and the final report.
- Record names, student IDs, issues, commits, annotations and writing contributions.

### 16.3 Original eight-week work plan — must be re-estimated

The table is the historical two-venue baseline. It is not a commitment for 31
planned editions. Before future collection, budget adapter/source access work,
390 cumulative diagnostic papers if all additions qualify, annotation scenarios
and each reviewer's available hours. Preserve independent review and release gates.

| Week | Person A | Person B | Shared output and exit gate |
| --- | --- | --- | --- |
| 1 | Source access, corpus configuration and identity/schema draft | Topic taxonomy, parser pilot and annotation guide | 100-paper pilot; relation inventory and proposed accuracy definition reviewed |
| 2 | Full official roster, metadata collection and logs | Header extraction, source-field checks and development labels | Reconciled corpus; no systemic extraction defect |
| 3 | Entity resolution, alias tables and affiliation triples | Topic baseline/classifier and independent gold annotations | Canonical entities; uncertain cases quantified; label guide stabilized |
| 4 | Neo4j schema, factual imports and provenance checks | Calibrated topic decisions, held-out evaluation and EDA draft | Frozen taxonomy/model; test separation respected; initial factual graph |
| 5 | R7–R10 derivation, integrity tests and frozen audit exports | Audit coordination, per-type checks and error analysis | All ten types present; size gates pass; both review audit evidence |
| 6 | Named projections, graph metrics and quality fixes | Communities, portfolios, citations and business cases | Measured precision/recall/coverage; robust, source-supported findings |
| 7 | Clean rebuild, exports, setup instructions and query checks | Minimal demo, report integration and final figures | Each person reproduces the other's principal results; release candidate |
| 8 | Final graph/code release and reproducibility check | Final report, presentation and demo script | Joint rubric review, disclosed limitations and final submission |

### 16.4 Workload guardrails

- Keep the eight-week schedule as a baseline, not a known course deadline.
- Estimate annotation/review effort in week one using both people's availability.
- Freeze the expanded registry/year/track version before future acquisition; changes require a documented scope revision, never silent omission of a hard-to-access venue.
- Use existing parsing/embedding tools; avoid training a general NER model from scratch.
- Use metadata-first collection and selective PDF processing.
- Keep the demo small and prioritize quality evaluation.
- Start report sections as methods freeze; reserve week eight for integration and correction.
- If time is tighter, remove optional years, prediction and extra UI features first.
- If the corpus must be narrowed, choose a complete edition, disclose the boundary and recheck all rubric requirements.
- Preserve independent review and quality thresholds when reducing scope.

## 17 Report structure and submission package

### 17.1 Report outline

- Course minimum: **10 pages**.
- Planning target: **16–18 substantive pages**, excluding cover and optional appendices.
- Describe completed behavior and measured results; mark any unmet target explicitly.

| Report section | Suggested pages | Required content |
| --- | --- | --- |
| Problem and business motivation | 1 | Scope, decisions supported, research questions, boundary |
| Team allocation | 0.5 | Named responsibilities, reviewers, contribution evidence |
| Sources and collection | 1.5 | Proceedings selection, stack, access, manifest, counts, provenance |
| Preprocessing and entity resolution | 2 | Cleaning, author/organization matching, version handling, paper-time affiliations |
| NLP methods | 2 | Header parsing, topic taxonomy, baseline/model, splits, annotation |
| Graph design and construction | 2 | Node meanings, ten relation types, derivation rules, DBMS, weights |
| EDA and network statistics | 1.5 | Completeness, size by type, projection statistics, diagnostic plots |
| Social network and business analysis | 2.5 | Centrality, communities, sectors, topics, citations, case studies |
| Quality and robustness | 2 | Precision audit, intervals, recall/F1, coverage, error categories, sensitivity |
| Conclusion and limitations | 1 | Achievements, unmet targets, selection bias, boundary and missingness limits |
| References and reproducibility | 1 | Primary documentation, repository URL, release tag, run instructions |

### 17.2 Submission package

- Final report PDF and real GitHub URL/release tag.
- Setup, acquisition and rebuild instructions.
- Official source manifest and data dictionary.
- Graph schema and permitted node/edge exports.
- Evidence ledger and measured quality tables.
- Neo4j export or reproducible load path.
- Contribution table; optional short demo recording.

### 17.3 README and release rules

- Lead with scope and measured results.
- Define all ten relationships and link the schema/report.
- Give exact setup/run commands and versions.
- State coverage and selection limitations.
- Exclude credentials and unredistributable inputs.
- Keep the code license distinct from third-party paper/data rights.

## 18 Risks and fallback decisions

### 18.1 Risks and responses

| Risk | Early signal | Response |
| --- | --- | --- |
| Historical affiliations overwritten by current profiles | Many papers inherit one person’s latest organization | Require paper-specific evidence; rederive downstream organization edges |
| Incorrect researcher merges | Common-name hubs with incompatible coauthors or institutions | Split identities, retain reversible decisions, audit top hubs |
| Missing or ambiguous affiliation mappings | Good organization lists but no author-level alignment | Preserve mentions, review selected sources, withhold unsupported links, report coverage |
| Topic classifier has high precision only at low coverage | Many abstentions or a few dominant labels | Improve taxonomy/rules on development data, add reviewed labels, disclose recall and coverage |
| Insufficient evidence for all ten predicates | A derived type remains empty or rare | Inspect scope and support rules; add justified complete editions if feasible; ask lecturer to review the schema early |
| Citation subgraph is sparse | Few in-core references | Report boundary effect; add a separate bounded context or adjacent complete years after quality passes |
| Source access or API allowance limits | Repeated quota errors or changing fields | Cache, use manifest-based acquisition, slow/resume collection, fall back to official records and PDFs |
| Manual review exceeds capacity | Pilot review minutes scale beyond available effort | Prioritize systemic fixes and core scope; reduce optional features before reducing audit quality |
| DBMS algorithm or memory mismatch | GDS compatibility failure or projection exceeds memory | Pin compatible versions, use smaller named projections, verify a documented algorithm fallback |
| Attractive but unsupported business claims | Rankings lack evidence or ignore missing data | Require case-study source support and boundary/coverage statements |

### 18.2 Two-person delivery priorities

1. Correct systematic extraction and resolution errors.
2. Complete the core graph and independent audit.
3. Produce the required analyses and report.
4. Add optional features only after the release gates pass.

### 18.3 Limitations to acknowledge

- Curated flagship AI/related conference selection and English scientific text; journals, regional venues, excluded tracks and no-edition years remain outside the boundary.
- Unequal venue sizes, publisher access and extraction/matching coverage can distort cross-field rankings. Report per-venue completeness and compare normalized as well as raw participation.
- The historical NeurIPS/ICML pilot provides no measured coverage or accuracy guarantee for newly planned venues.
- Incomplete bibliographic, affiliation or citation coverage.
- Unresolved people and uncertain organizational hierarchy.
- Corpus-boundary effects on centrality and communities.
- Publication evidence differs from current real-world relationships.
- A sparse or fragmented graph can still be a correct result.

## 19 First implementation steps and definition of done

### 19.1 Next planning and offline implementation steps

Collection is paused. Review the registry and track policies; generalize official
source adapters, edition IDs, venue labels and staged split quotas using offline
fixtures. Preserve old held-out IDs and design supplemental leakage groups,
annotation hours, source rights and access routes before asking for a collection
run. Review current pilot identity/affiliation gaps and draft taxonomy coverage.
After a later collection instruction, run venue-specific diagnostics and revise
resources/schedule before full acquisition.

The following three-day table is historical pilot guidance, not a new run request.

| When | Person A | Person B | Joint checkpoint |
| --- | --- | --- | --- |
| Day 1 | Create source manifest, repository and canonical-ID proposal | Draft topic guide, gold-label format and NLP pilot | Agree corpus, ten predicates and proposed accuracy definition |
| Day 2 | Test source matching, affiliation triples and review logs | Test GROBID on varied layouts and label a small sample | Inspect 20 affiliation mappings and difficult identity cases |
| Day 3 | Build the small graph and verify repeatable import | Review semantic outputs and estimate annotation effort | Freeze pilot decisions, check workload and confirm next milestone |

### 19.2 Final release checklist

- [ ] The expanded venue/year/track registry is frozen; its ledger reconciles every included, excluded, no-edition, unavailable, failed and unresolved record.
- [ ] At least 2,000 resolved researchers and 5,000 unique accepted factual edges are present.
- [ ] All ten predicates have genuine support, documented semantics, and separate counts.
- [ ] Author-specific affiliations are traceable to individual papers.
- [ ] Identity aliases, version merges, institution rollups, and unknowns are documented.
- [ ] NLP baseline, accepted method, gold set, and held-out results are reproducible.
- [ ] Global audit and per-type audits report exact correct/total counts and appropriate uncertainty.
- [ ] Recall and coverage are shown alongside precision, including abstentions and unresolved records.
- [ ] Analysis uses named projections with correct directions, weights, and boundary labels.
- [ ] Three business case studies provide source support and material limitations.
- [ ] Both teammates can reproduce the graph and principal analysis outputs.
- [ ] Report meets the page requirement and contains the real repository URL and both members' contributions.

## 20 Primary sources and implementation references

- Original documentation/research checks date to **1 November 2026**. The **3 November scope revision** adds official catalog leads below; their per-edition sources, tracks, access and rights have not been verified through new corpus discovery.
- Recheck source access and pin software APIs during implementation.
- Thresholds, workload estimates and method choices are project recommendations, not guaranteed outcomes.

| Reference | Source and URL | Relevance |
| --- | --- | --- |
| S1 | NeurIPS proceedings index — https://proceedings.neurips.cc/ | Official editions and the placement of Datasets and Benchmarks papers |
| S2 | NeurIPS 2023 proceedings — https://proceedings.neurips.cc/paper/2023 | Core NeurIPS paper roster and track metadata |
| S3 | ICML 2023 PMLR volume 202 — https://proceedings.mlr.press/v202/ | Core ICML roster, metadata, abstracts, and PDFs |
| S4 | ICML 2022 volume 162 and ICML 2024 volume 235 — https://proceedings.mlr.press/v162/ and https://proceedings.mlr.press/v235/ | Optional complete temporal editions |
| S5 | OpenAlex authorships — https://help.openalex.org/data/authorships/ | Author-specific affiliation fields, raw strings, and authorship-list limitations |
| S6 | OpenAlex work attributes — https://help.openalex.org/data/works/attributes/ | Work identifiers, authorships, and outgoing references |
| S7 | OpenAlex authentication — https://help.openalex.org/api/authentication/ | Current key, paging, rate-limit, and usage guidance |
| S8 | OpenAlex pricing overview — https://help.openalex.org/access/pricing/ | Free allowance and usage-based service model |
| S9 | OpenReview custom submission export — https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-loop-through-accepted-papers-and-print-the-authors-and-their-affiliations | Submission/profile structure and the distinction between profile affiliations and paper evidence |
| S10 | GROBID service API — https://grobid.readthedocs.io/en/latest/Grobid-service/ | Header extraction, full-text extraction, TEI, and consolidation controls |
| S11 | ROR affiliation matching — https://ror.readme.io/docs/api-affiliation | Organization resolution, chosen matches, ambiguity, and fallback review |
| S12 | GROBID end-to-end evaluation — https://grobid.readthedocs.io/en/latest/End-to-end-evaluation/ | Extraction and linked author–affiliation evaluation design |
| S13 | Sentence Transformers semantic similarity — https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html | Text embeddings and similarity computation |
| S14 | Cohan et al. 2020 SPECTER — https://aclanthology.org/2020.acl-main.207/ | Original scientific-document embedding research |
| S15 | Neo4j GDS introduction — https://neo4j.com/docs/graph-data-science/current/introduction/ | Named projections, algorithm traits, editions and limits |
| S16 | Neo4j GDS Leiden — https://neo4j.com/docs/graph-data-science/current/algorithms/leiden/ | Community detection implementation |
| S17 | Neo4j GDS PageRank — https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/ | Directed influence analysis implementation |
| S18 | NetworkX Louvain — https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html | Community detection fallback and independent checks |
| S19 | Neo4j Cypher constraint syntax — https://neo4j.com/docs/cypher-manual/current/schema/syntax/ | Idempotent uniqueness constraints for schema setup |
| S20 | ICLR / OpenReview — https://openreview.net/group?id=ICLR.cc | Official conference groups and acceptance/track evidence; verify 2023 main conference |
| S21 | CVF / ECVA — https://openaccess.thecvf.com/ and https://www.ecva.net/papers.php | Vision conference proceedings; distinguish main/workshop and no-edition years |
| S22 | ACL Anthology — https://aclanthology.org/venues/ | ACL-family event/year/track metadata; separate Findings, demos and workshops |
| S23 | AAAI / ICAPS — https://ojs.aaai.org/ | Official archival conference records and research-track mapping |
| S24 | IJCAI — https://www.ijcai.org/proceedings/ | Official edition and main research paper records |
| S25 | ACM Digital Library — https://dl.acm.org/ | KDD, WWW, SIGIR, WSDM, RecSys, CIKM and ACM Multimedia official metadata; check rights/access |
| S26 | IEEE Xplore — https://ieeexplore.ieee.org/browse/conferences/title | ICDM, ICRA and IROS edition metadata; use lawful permitted access |
| S27 | SIAM / MICCAI — https://epubs.siam.org/conference/sdm and https://www.miccai.org/index.php/publications/ | SDM and medical-imaging proceedings leads; resolve exact edition and rights |
| S28 | Dedicated proceedings — https://www.roboticsproceedings.org/ ; https://www.ifaamas.org/Proceedings/ ; https://proceedings.kr.org/ | RSS, AAMAS and KR official source families |
| S29 | PMLR / MLSys — https://proceedings.mlr.press/ and https://proceedings.mlsys.org/ | Learning/theory/robot learning/system conference volumes; verify per-edition identifiers |
