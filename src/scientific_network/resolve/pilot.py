"""Conservative pilot: public ORCID publication corroboration and PDF-aligned institutions."""

from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from scientific_network.collect.acquire import normalize, names_compatible
from scientific_network.collect.storage import SourceCache, SourceError, QuotaError, digest, write_json, read_config
from scientific_network.contracts import GraphArtifact, Node, Edge, EvidenceRecord, AffiliationObservation, Relation as R
from scientific_network.graph.schema import edge_id
from scientific_network.graph.validate import validate_graph, graph_counts

VERSION = "orcid-public-work-pdf-affiliation-v4-source-review"


def orcid_support(body: bytes, title: str, identifiers: set[str]) -> str | None:
    root = ET.fromstring(body)
    for group in root.findall("{*}group"):
        values = {normalize(e.text or "") for e in group.findall(".//{*}external-id-value")}
        titles = {normalize("".join(e.itertext())) for e in group.findall(".//{*}title")}
        if identifiers & values:
            return "public_work_identifier"
        if normalize(title) in titles:
            return "public_work_title"
    return None


def align_header(name: str, headers: list[dict]) -> dict | None:
    matches = [author for author in headers if names_compatible(name, author["name"])]
    return matches[0] if len(matches) == 1 else None


def match_institution(printed: str, institutions: list[dict]) -> dict | None:
    matches = {inst["id"]: inst for inst in institutions if normalize(printed) == normalize(inst.get("display_name", ""))}
    return next(iter(matches.values())) if len(matches) == 1 else None


def reviewed_institution(decision: dict, record: dict) -> dict:
    """A printed, author-specific observation; never an alias or identity override."""
    position = decision["byline_position"]
    names = record["official"]["authors"]
    if not isinstance(position, int) or not 1 <= position <= len(names) or not names_compatible(names[position-1], decision["raw_name"]):
        raise ValueError("reviewed affiliation has a different byline position/name")
    if decision.get("pdf_sha256") != (record.get("pdf_source") or {}).get("sha256"):
        raise ValueError("reviewed affiliation is not bound to this paper PDF")
    if not decision.get("decision_id") or not decision.get("source_locator"):
        raise ValueError("reviewed affiliation requires a decision ID and printed locator")
    work = record.get("openalex_work") or {}
    authorships = work.get("authorships", [])
    if len(authorships) != len(names):
        raise ValueError("reviewed affiliation requires complete matched authorship metadata")
    inst = match_institution(decision["printed_institution"], authorships[position-1].get("institutions", []))
    if inst is None or inst["id"] != decision["openalex_institution_id"]:
        raise ValueError("reviewed printed institution lacks exact authorship-specific corroboration")
    return inst


def resolve(input_path: Path, output: Path, cache_path: Path, config_path: Path,
            decisions_path: Path | None = None) -> dict:
    papers = json.loads(input_path.read_text())
    config = read_config(config_path)
    venue_names = {e["venue_id"]: e["name"] for e in config["editions"]}
    allowed = {(edition["venue_id"], edition["year"], track)
        for edition in config["editions"] for track in edition["include_tracks"]}
    for record in papers:
        if record.get("status") == "acquired":
            row = record["roster"]
            if (row["venue_id"], row["year"], row["track"]) not in allowed:
                raise ValueError("paper falls outside configured core corpus")
    source_reviews, reviewed_affiliations = {}, defaultdict(list)
    if decisions_path:
        decision_file = json.loads(decisions_path.read_text())
        if decision_file.get("reviewed_input_sha256") != digest(input_path.read_bytes()):
            raise ValueError("source review does not match the resolution input")
        by_id = {r["paper_id"]: r for r in papers}
        for decision in decision_file["decisions"]:
            paper_id = decision["paper_id"]
            if paper_id in source_reviews or paper_id not in by_id:
                raise ValueError("duplicate or unknown source-review paper ID")
            if decision.get("disposition") not in {"retain_source_byline", "withhold_core"}:
                raise ValueError("source review cannot override identities or affiliations")
            if decision.get("record_sha256") != digest(json.dumps(by_id[paper_id], sort_keys=True, ensure_ascii=False).encode()):
                raise ValueError("reviewed paper record has changed")
            if not decision.get("decision_id") or not decision.get("reason") or not decision.get("evidence"):
                raise ValueError("source review requires an ID, reason and evidence")
            for proof in decision["evidence"]:
                if digest((cache_path / "objects" / proof["sha256"]).read_bytes()) != proof["sha256"]:
                    raise ValueError("source review evidence hash mismatch")
            source_reviews[paper_id] = decision
        seen_affiliations = set()
        for decision in decision_file.get("reviewed_affiliations", []):
            record = by_id[decision["paper_id"]]
            key = (decision["paper_id"], decision["byline_position"], decision["openalex_institution_id"])
            if key in seen_affiliations:
                raise ValueError("duplicate reviewed affiliation observation")
            seen_affiliations.add(key)
            if decision.get("record_sha256") != digest(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()):
                raise ValueError("reviewed affiliation paper record has changed")
            reviewed_institution(decision, record)
            if digest((cache_path / "objects" / decision["pdf_sha256"]).read_bytes()) != decision["pdf_sha256"]:
                raise ValueError("reviewed affiliation PDF hash mismatch")
            reviewed_affiliations[decision["paper_id"], decision["byline_position"]].append(decision)
    graph_version = "pilot-" + digest(VERSION.encode() + input_path.read_bytes() + config_path.read_bytes()
        + (decisions_path.read_bytes() if decisions_path else b""))[:12]
    nodes, edges, evidence, observations, reviews = {}, {}, {}, {}, []
    applied_reviewed_affiliations = set()
    matched_work_counts = Counter(r["openalex_work"]["id"] for r in papers
        if r.get("status") == "acquired" and r.get("openalex_work"))
    duplicate_works = {identifier for identifier, count in matched_work_counts.items() if count > 1}

    def source(record, kind="observed", locator="record", excerpt=None):
        identifier = "evidence:" + digest(f"{record['sha256']}|{locator}|{kind}".encode())
        evidence[identifier] = EvidenceRecord(id=identifier, kind=kind, source_url=record["url"],
            retrieved_at=record["retrieved_at"], raw_sha256=record["sha256"], source_locator=locator, excerpt=excerpt)
        return identifier

    def add(relation, left, right, support, **props):
        identifier = edge_id(R(relation), left, right)
        if identifier in edges:
            edge = edges[identifier]
            edge.evidence_ids = sorted(set(edge.evidence_ids + support))
            if "observed_years" in props:
                edge.properties["observed_years"] = sorted(set(edge.properties["observed_years"] + props["observed_years"]))
            return
        edges[identifier] = Edge(edge_id=identifier, relation=relation, source_id=left, target_id=right,
            evidence_kind="observed", evidence_ids=sorted(set(support)), method_version=VERSION,
            graph_version=graph_version, validation_status="accepted", properties=props)

    def add_affiliation(researcher_id, paper_id, inst, support, year):
        organization_id = "organization:" + inst["id"].rsplit("/", 1)[-1]
        nodes[organization_id] = Node(id=organization_id, label="Organization", name=inst["display_name"], properties={
            "sector": {"education": "academia", "company": "industry", "government": "government", "nonprofit": "nonprofit"}.get(inst.get("type"), "unknown"),
            "ror": inst.get("ror"), "country_code": inst.get("country_code"),
            "normalization_policy": "exact_printed_name_plus_authorship_specific_openalex_institution"})
        obs_id = "affiliation:" + digest(f"{researcher_id}|{paper_id}|{organization_id}".encode())
        previous = observations.get(obs_id)
        observations[obs_id] = AffiliationObservation(id=obs_id, researcher_id=researcher_id,
            paper_id=paper_id, organization_id=organization_id,
            evidence_ids=sorted(set(support + (previous.evidence_ids if previous else []))))
        add("AFFILIATED_WITH", researcher_id, organization_id, support, observed_years=[year])

    # A provider identity with conflicting ORCIDs or repeated on one byline is withheld.
    provider_orcids = defaultdict(set)
    blocked_providers = set()
    blocked_orcids = set()
    for record in papers:
        work = record.get("openalex_work") or {}
        author_ids = []
        byline_orcids = []
        for a in work.get("authorships", []):
            author = a.get("author") or {}
            author_ids.append(author.get("id"))
            if author.get("orcid"):
                provider_orcids[author.get("id")].add(author["orcid"])
                byline_orcids.append(author["orcid"])
        blocked_providers.update(key for key, count in Counter(author_ids).items() if count > 1)
        blocked_orcids.update(key for key, count in Counter(byline_orcids).items() if count > 1)
    blocked_providers.update(key for key, values in provider_orcids.items() if len(values) > 1)

    with SourceCache(cache_path, delay=0.15,
        timeout=config["retrieval"]["timeout_seconds"], attempts=config["retrieval"]["max_attempts"]) as cache:
        for number, record in enumerate(papers, 1):
            if record.get("status") != "acquired":
                continue
            row, paper = record["roster"], record["official"]
            paper_id, venue_id = record["paper_id"], row["venue_id"]
            if source_reviews.get(paper_id, {}).get("disposition") == "withhold_core":
                decision = source_reviews[paper_id]
                reviews.append({"paper_id": paper_id, "reason": "reviewed_source_byline_conflict",
                    "decision_id": decision["decision_id"], "source_review_reason": decision["reason"]})
                continue
            if (record.get("openalex_work") or {}).get("id") in duplicate_works:
                reviews.append({"paper_id": paper_id, "reason": "shared_provider_work_requires_version_review",
                    "openalex_work_id": record["openalex_work"]["id"]})
                continue
            nodes[venue_id] = Node(id=venue_id, label="Venue", name=venue_names[venue_id])
            nodes[paper_id] = Node(id=paper_id, label="Paper", name=paper["title"], properties={
                "year": row["year"], "official_url": row["official_url"], "track": row["track"],
                "is_core": True, "abstract": paper["abstract"], "official_author_count": len(paper["authors"]),
                "unresolved_author_reason": "withhold identities lacking public publication corroboration"})
            roster_source = {"url": row["source_url"], "sha256": row["source_sha256"], "retrieved_at": row["retrieved_at"]}
            official_evidence = source(roster_source, locator=row["source_locator"])
            nodes[paper_id].properties["topic_text_evidence_id"] = source(record["official_source"],
                locator=paper.get("title_locator", "meta[name=citation_title]") + ";" + paper.get("abstract_locator", "official_abstract"))
            add("PUBLISHED_IN", paper_id, venue_id, [official_evidence])
            work = record.get("openalex_work")
            if not work:
                reviews.append({"paper_id": paper_id, "reason": record.get("match_decision", "unmatched_work")})
                continue
            oa_evidence = source(record["openalex_source"], locator=f"results[id={work['id']}].authorships")
            for position, (name, authorship) in enumerate(zip(paper["authors"], work["authorships"]), 1):
                author = authorship["author"]
                orcid = (author.get("orcid") or "").removeprefix("https://orcid.org/")
                base = {"paper_id": paper_id, "byline_position": position, "raw_name": name,
                        "openalex_author_id": author.get("id")}
                if not re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", orcid) or author.get("id") in blocked_providers or author.get("orcid") in blocked_orcids:
                    reviews.append({**base, "reason": "no_unambiguous_corroborated_identifier"})
                    continue
                orcid_url = f"https://pub.orcid.org/v3.0/{orcid}/works"
                try:
                    body, orcid_record = cache.get(orcid_url)
                    ids = {normalize(v.removeprefix("https://doi.org/")) for v in [paper.get("doi"), work.get("doi")] if v}
                    reason = orcid_support(body, paper["title"], ids)
                except QuotaError as exc:
                    if "429" in str(exc):
                        raise
                    reason = None
                except (SourceError, ET.ParseError):
                    reason = None
                if reason is None:
                    reviews.append({**base, "reason": "orcid_publication_not_corroborated"})
                    continue
                researcher_id = "researcher:orcid:" + orcid
                if researcher_id in nodes and not names_compatible(nodes[researcher_id].name, name):
                    raise ValueError("ORCID/name contradiction; split decision requires review")
                orcid_evidence = source(orcid_record, locator=f"work-summary[title_or_identifier_matches={paper_id}]")
                previous = nodes.get(researcher_id)
                previous_properties = previous.properties if previous else {}
                nodes[researcher_id] = Node(id=researcher_id, label="Researcher", name=name,
                    properties={"resolution_status": "resolved", "orcid": orcid,
                        "openalex_ids": sorted(set(previous_properties.get("openalex_ids", []) + [author["id"]])),
                        "name_variants": sorted(set(previous_properties.get("name_variants", []) + [name])),
                        "identity_method": reason, "independent_audit": "pending"})
                byline_evidence = source(roster_source if paper.get("authors_from_roster") else record["official_source"], locator=f"{paper.get("author_locator", "meta[name=citation_author]")}[{position}]")
                add("AUTHORED", researcher_id, paper_id, [byline_evidence, oa_evidence, orcid_evidence], byline_position=position)
                for decision in reviewed_affiliations.get((paper_id, position), []):
                    inst = reviewed_institution(decision, record)
                    proof = source(record["pdf_source"], locator=decision["source_locator"] + ";decision=" + decision["decision_id"])
                    add_affiliation(researcher_id, paper_id, inst, [proof, oa_evidence], row["year"])
                    applied_reviewed_affiliations.add(decision["decision_id"])
                header = align_header(name, record.get("header_authors", []))
                if header is None:
                    reviews.append({**base, "reason": "pdf_author_alignment_missing_or_ambiguous"})
                    continue
                for affiliation in header["affiliations"]:
                    for printed in affiliation["institutions"]:
                        inst = match_institution(printed, authorship.get("institutions", []))
                        if inst is None:
                            reviews.append({**base, "reason": "printed_institution_needs_canonical_review", "printed_institution": printed})
                            continue
                        pdf_evidence = source(record["pdf_source"], locator=f"tei_sha256={record['tei_source']['sha256']}:{affiliation['locator']}")
                        support = [pdf_evidence, oa_evidence]
                        add_affiliation(researcher_id, paper_id, inst, support, row["year"])
            if number % 10 == 0:
                print(f"resolve: {number}/{len(papers)} pilot papers", flush=True)
    # Citation targets must resolve to another acquired core work, never a title guess.
    work_to_paper = defaultdict(list)
    for record in papers:
        if record.get("openalex_work") and record["paper_id"] in nodes:
            work_to_paper[record["openalex_work"]["id"]].append(record["paper_id"])
    for record in papers:
        work = record.get("openalex_work")
        if not work or record["paper_id"] not in nodes:
            continue
        for target in set(work.get("referenced_works", [])):
            targets = work_to_paper.get(target, [])
            if len(targets) == 1 and targets[0] != record["paper_id"]:
                add("CITES", record["paper_id"], targets[0],
                    [source(record["openalex_source"], locator=f"results[id={work['id']}].referenced_works[{target}]")])
    graph = GraphArtifact(graph_version=graph_version, is_synthetic=False,
        nodes=sorted(nodes.values(), key=lambda n: n.id), edges=sorted(edges.values(), key=lambda e: e.edge_id),
        evidence=sorted(evidence.values(), key=lambda e: e.id),
        affiliation_observations=sorted(observations.values(), key=lambda a: a.id))
    errors = validate_graph(graph)
    if errors:
        raise ValueError("resolved graph failed structural checks: " + "; ".join(errors[:5]))
    write_json(output / "graph.json", json.loads(graph.model_dump_json()))
    write_json(output / "review-queue.json", reviews)
    summary = {"stage": "resolve", "method_version": VERSION, "input_sha256": digest(input_path.read_bytes()),
        "config_sha256": digest(config_path.read_bytes()),
        "source_review_sha256": digest(decisions_path.read_bytes()) if decisions_path else None,
        "reviewed_affiliation_decisions_applied": len(applied_reviewed_affiliations),
        "graph_version": graph_version, "counts": graph_counts(graph),
        "review_reasons": dict(Counter(row["reason"] for row in reviews)),
        "affiliation_observations": len(observations), "semantic_accuracy": "not_measured"}
    write_json(output / "summary.json", summary)
    return summary
