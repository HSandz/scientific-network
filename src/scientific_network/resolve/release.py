"""Release graph builder (D040, release plan Phase 3): roster + OpenAlex works to a GraphArtifact.

Evidence rules (plan section 2.2). A researcher is the OpenAlex author ID at the same byline
position as a name-compatible roster name; names are never merged on their own. An
institution with an OpenAlex ID on that authorship is an affiliation, with the raw
affiliation string kept as evidence, and an institution without an ID is unknown. Citations
link only matched in-scope works. Everything withheld goes to the review queue with a reason,
and a paper that keeps only its venue edge carries an ``unresolved_author_reason``.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from scientific_network.collect.acquire import name_tokens, names_compatible
from scientific_network.collect.storage import read_config, read_jsonl, write_bytes, write_json
from scientific_network.contracts import (
    AffiliationObservation, Edge, EvidenceRecord, GraphArtifact, Node,
)
from scientific_network.graph.materialize import materialize
from scientific_network.graph.schema import edge_id
from scientific_network.graph.validate import graph_counts, validate_graph
from scientific_network.nlp.baseline import METHOD as TOPIC_METHOD, predict

METHOD_VERSION = "release-openalex-graph-v1.3"
SECTOR = {"education": "academia", "company": "industry", "government": "government", "nonprofit": "nonprofit"}
VENUES = {
    "venue:aaai": "AAAI Conference on Artificial Intelligence",
    "venue:ijcai": "International Joint Conference on Artificial Intelligence",
}
# The existing public Site is the taxonomy's resolvable home (D019/D020); the config hash is the evidence.
TAXONOMY_SOURCE_URL = "https://ai-research-network-plan.hazy-tern-8113.chatgpt.site"
ORCID = re.compile(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dXx])")


def short_id(value) -> str | None:
    """``https://openalex.org/A123`` -> ``A123``; None when not an OpenAlex ID."""
    text = str(value or "").strip().rstrip("/")
    tail = text.rsplit("/", 1)[-1]
    return tail if re.fullmatch(r"[A-Z]\d+", tail) else None


def normalize_orcid(value) -> str | None:
    match = ORCID.search(str(value or ""))
    return match[1].upper() if match else None


def _sha(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


# --- names ---------------------------------------------------------------------------------------


def names_initials_compatible(left: str, right: str) -> bool:
    """Initials-tolerant comparison: every token of the shorter name matches a distinct token of the
    longer one, exactly or as an initial, and at least one full-word token matches exactly."""
    a, b = name_tokens(left), name_tokens(right)
    if not a or not b:
        return False
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    pool, exact = list(long_), 0
    for token in short:
        if token in pool:
            pool.remove(token)
            exact += len(token) > 1
            continue
        initial = next((other for other in pool if (len(token) == 1 and other.startswith(token))
                        or (len(other) == 1 and token.startswith(other))), None)
        if initial is None:
            return False
        pool.remove(initial)
    return exact >= 1


def name_match(roster_name: str, authorship: dict, allow_initials: bool) -> str | None:
    """'exact' when a printed or canonical OpenAlex name has the same tokens, 'initials' if tolerated."""
    candidates = [authorship.get("raw_author_name"), (authorship.get("author") or {}).get("display_name")]
    candidates = [name for name in candidates if name]
    if any(names_compatible(roster_name, name) for name in candidates):
        return "exact"
    if allow_initials and any(names_initials_compatible(roster_name, name) for name in candidates):
        return "initials"
    return None


# --- affiliations --------------------------------------------------------------------------------


def authorship_institutions(authorship: dict) -> list[dict]:
    """Institutions with an OpenAlex ID on this authorship and the raw strings that map to each.

    ``affiliations`` (raw string -> institution IDs) is preferred; without it every raw string is
    attached to every institution, which the evidence field then says plainly.
    """
    mapped: dict[str, list[str]] = defaultdict(list)
    for affiliation in authorship.get("affiliations") or []:
        raw = (affiliation.get("raw_affiliation_string") or "").strip()
        for institution_id in affiliation.get("institution_ids") or []:
            if raw and raw not in mapped[short_id(institution_id) or ""]:
                mapped[short_id(institution_id) or ""].append(raw)
    fallback = [s.strip() for s in authorship.get("raw_affiliation_strings") or [] if s and s.strip()]
    result, seen = [], set()
    for institution in authorship.get("institutions") or []:
        identifier = short_id(institution.get("id"))
        if identifier is None or identifier in seen:
            continue
        seen.add(identifier)
        result.append({
            "id": identifier, "name": institution.get("display_name") or identifier,
            "ror": institution.get("ror"), "country_code": institution.get("country_code"),
            "type": institution.get("type"),
            "raw_strings": mapped.get(identifier) or fallback,
            "raw_string_mapping": "affiliations" if mapped.get(identifier) else "authorship_level",
        })
    return result


# --- build ---------------------------------------------------------------------------------------


def _work_evidence(row: dict) -> EvidenceRecord:
    source = row["openalex"]["source"]
    work_id = short_id(row["openalex"]["id"])
    return EvidenceRecord(
        id="evidence:openalex:" + _sha(row["paper_id"], source["raw_sha256"])[:24], kind="observed",
        source_url=f"https://openalex.org/{work_id}", retrieved_at=source["retrieved_at"],
        raw_sha256=source["raw_sha256"], source_locator=f"openalex-request:{source['request_id']}#{source['locator']}",
    )


def _roster_evidence(row: dict) -> EvidenceRecord:
    roster = row["roster"]
    return EvidenceRecord(
        id="evidence:roster:" + _sha(row["paper_id"], roster["source_sha256"])[:24], kind="observed",
        source_url=roster["source_url"], retrieved_at=roster["retrieved_at"], raw_sha256=roster["source_sha256"],
        source_locator=roster["source_locator"],
    )


def build_release_graph(
    works_path: Path, config_path: Path, taxonomy_path: Path, quality_path: Path, output_dir: Path, summary_path: Path,
) -> dict:
    config, taxonomy, quality = read_config(config_path), read_config(taxonomy_path), read_config(quality_path)
    allow_initials = bool(config["matching"].get("initials_tolerant", False))
    guard = config["matching"]["paper_level_copy_guard"]
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("release graph output directory is not empty; use a new versioned directory")
    rows = read_jsonl(works_path)
    inputs = {"works": _sha(works_path.read_text(encoding="utf-8")), "config": _sha(config_path.read_text()),
              "taxonomy": _sha(taxonomy_path.read_text()), "quality": _sha(quality_path.read_text())}
    graph_version = "release-" + _sha(METHOD_VERSION, TOPIC_METHOD, *inputs.values())[:12]

    review: list[dict] = []
    counters = Counter()
    nodes: dict[str, Node] = {}
    edges: dict[str, Edge] = {}
    evidence: dict[str, EvidenceRecord] = {}
    observations: list[AffiliationObservation] = []

    def add_edge(relation, source, target, kind, evidence_ids, method, properties=None):
        identifier = edge_id(relation, source, target)
        if identifier in edges:
            return edges[identifier]
        edges[identifier] = Edge(
            edge_id=identifier, relation=relation, source_id=source, target_id=target, evidence_kind=kind,
            evidence_ids=evidence_ids, method_version=method, graph_version=graph_version,
            validation_status="accepted", properties=properties or {})
        return edges[identifier]

    # Complete-source identity pass, shared with the frozen-prediction correction.
    from scientific_network.resolve.release_identity import collect_identity_evidence
    identity = collect_identity_evidence(rows)
    orcids, identity_withheld = identity["orcids"], identity["withheld"]
    review.extend(identity["review"])

    # ---- venues, papers, authorships, affiliations
    for venue_id, name in VENUES.items():
        nodes[venue_id] = Node(id=venue_id, label="Venue", name=name, properties={})
    work_to_paper: dict[str, set[str]] = defaultdict(set)
    accepted_papers: dict[str, dict] = {}
    for row in rows:
        paper_id, roster = row["paper_id"], row["roster"]
        matched = row["match"]["status"] == "matched"
        properties = {
            "year": row["year"], "official_url": roster["official_url"], "pdf_url": roster["pdf_url"], "track": row["track"],
            "is_core": True, "official_author_count": len(roster["authors"]), "doi": row["doi"],
        }
        reason = None
        roster_evidence = _roster_evidence(row)
        evidence[roster_evidence.id] = roster_evidence
        if not matched:
            reason = "work_" + row["match"]["status"] + ":" + ",".join(row["match"]["reasons"])
            review.append({"kind": "work_not_accepted", "paper_id": paper_id, "status": row["match"]["status"],
                           "reasons": row["match"]["reasons"], "candidates": row.get("review_candidates")})
            counters["papers_unmatched"] += 1
        else:
            oa = row["openalex"]
            properties["openalex_id"] = short_id(oa["id"])
            work_to_paper[short_id(oa["id"])].add(paper_id)
            for alternate in oa.get("alternates", []):
                work_to_paper[short_id(alternate["id"])].add(paper_id)
            work_evidence = _work_evidence(row)
            evidence[work_evidence.id] = work_evidence
            authorships = oa["authorships"]
            positions = []        # (index, authorship, name_match_kind)
            unusable = []         # (index, reason): withheld one by one
            bad_names = 0         # name-incompatible positions: evidence the byline is misaligned
            for index, (name, authorship) in enumerate(zip(roster["authors"], authorships)):
                author_id = short_id((authorship.get("author") or {}).get("id"))
                kind = name_match(name, authorship, allow_initials)
                if kind is None:
                    bad_names += 1
                    unusable.append((index, "name_incompatible"))
                elif author_id is None:
                    unusable.append((index, "no_author_id"))        # name fits but OpenAlex has no ID: not a person node
                elif author_id in identity_withheld:
                    unusable.append((index, identity_withheld[author_id]))
                else:
                    positions.append((index, authorship, kind))
            ids = [short_id(a["author"]["id"]) for _, a, _ in positions]
            if bad_names > 1 or len(ids) != len(set(ids)):
                paper_withheld_reason = "multiple_incompatible_positions" if bad_names > 1 else "author_id_repeated_in_paper"
                reasons_by_position = {index: why for index, why in unusable}
                position_reviews = []
                for index, name in enumerate(roster["authors"]):
                    why = reasons_by_position.get(index, paper_withheld_reason)
                    position_reviews.append({"position": index + 1, "reason": why, "roster_name": name})
                    counters["author_positions_withheld_" + why] += 1
                review.append({"kind": "authorships_withheld_for_paper", "paper_id": paper_id, "reason": paper_withheld_reason,
                               "positions": position_reviews})
                counters["papers_all_authorships_withheld"] += 1
                counters["author_positions_withheld"] += len(roster["authors"])
                positions, unusable = [], []
                reason = "authorships_withheld:" + paper_withheld_reason
            elif unusable:
                for index, why in unusable:
                    review.append({"kind": "author_position_withheld", "paper_id": paper_id, "position": index + 1,
                                   "reason": why, "roster_name": roster["authors"][index]})
                    counters["author_positions_withheld_" + why] += 1
                counters["author_positions_withheld"] += len(unusable)
            counters["author_positions"] += len(authorships)
            counters["author_positions_accepted"] += len(positions)
            counters["author_positions_initials_match"] += sum(kind == "initials" for _, _, kind in positions)
            accepted_papers[paper_id] = {"row": row, "positions": positions, "evidence": work_evidence}
            if not positions and reason is None:
                reason = "no_accepted_authorship"
        if reason:
            properties["unresolved_author_reason"] = reason
        nodes[paper_id] = Node(id=paper_id, label="Paper", name=roster["title"], properties=properties)
        add_edge("PUBLISHED_IN", paper_id, row["venue_id"], "observed", [roster_evidence.id], METHOD_VERSION,
                 {"year": row["year"]})

    # authorships and affiliation triples
    pair_support: dict[tuple[str, str], dict] = {}
    for paper_id, info in sorted(accepted_papers.items()):
        work_evidence = info["evidence"]
        per_author = []
        for index, authorship, kind in info["positions"]:
            author = authorship["author"]
            researcher_id = "researcher:openalex:" + short_id(author["id"])
            values = orcids.get(short_id(author["id"]), set())
            orcid = next(iter(values)) if len(values) == 1 else None
            if researcher_id not in nodes:
                nodes[researcher_id] = Node(
                    id=researcher_id, label="Researcher", name=author.get("display_name") or short_id(author["id"]),
                    properties={"resolution_status": "resolved", "identity_method": "openalex_author_id",
                                "openalex_id": short_id(author["id"]), **({"orcid": orcid} if orcid else {})})
            roster_name = info["row"]["roster"]["authors"][index]
            add_edge("AUTHORED", researcher_id, paper_id, "observed", [work_evidence.id], METHOD_VERSION,
                     {"byline_position": index + 1, "roster_name": roster_name, "name_match": kind})
            per_author.append((researcher_id, authorship_institutions(authorship)))
        institution_sets = [frozenset(i["id"] for i in insts) for _, insts in per_author]
        copied = (len(per_author) >= guard["min_authors"] and len(set(institution_sets)) == 1
                  and len(institution_sets[0]) >= guard["min_institutions"])
        if copied:
            review.append({"kind": "paper_level_affiliation_copy", "paper_id": paper_id,
                           "authors": len(per_author), "institutions": sorted(institution_sets[0])})
            counters["papers_affiliations_withheld_copy_guard"] += 1
            continue
        for researcher_id, institutions in per_author:
            counters["accepted_authorships_with_institution"] += bool(institutions)
            for institution in institutions:
                organization_id = "organization:" + institution["id"]
                if organization_id not in nodes:
                    nodes[organization_id] = Node(
                        id=organization_id, label="Organization", name=institution["name"],
                        properties={"sector": SECTOR.get(institution["type"], "unknown"),
                                    "openalex_id": institution["id"],
                                    **({"ror": institution["ror"]} if institution["ror"] else {}),
                                    **({"country_code": institution["country_code"]} if institution["country_code"] else {})})
                observations.append(AffiliationObservation(
                    id="affiliation:" + _sha(researcher_id, paper_id, organization_id)[:24], researcher_id=researcher_id,
                    paper_id=paper_id, organization_id=organization_id, evidence_ids=[work_evidence.id]))
                support = pair_support.setdefault((researcher_id, organization_id),
                                                  {"evidence": [], "papers": set(), "raw": []})
                support["papers"].add(paper_id)
                if work_evidence.id not in support["evidence"]:
                    support["evidence"].append(work_evidence.id)
                for raw in institution["raw_strings"]:
                    if raw not in support["raw"] and len(support["raw"]) < 5:
                        support["raw"].append(raw)
    for (researcher_id, organization_id), support in sorted(pair_support.items()):
        add_edge("AFFILIATED_WITH", researcher_id, organization_id, "observed", support["evidence"], METHOD_VERSION,
                 {"support_paper_count": len(support["papers"]), "raw_affiliation_strings": support["raw"]})

    # ---- citations among matched in-scope works
    for paper_id, info in sorted(accepted_papers.items()):
        for target in sorted({short_id(url) for url in info["row"]["openalex"]["referenced_works"]} - {None}):
            counters["reference_targets"] += 1
            papers = work_to_paper.get(target)
            if not papers:
                counters["reference_targets_out_of_scope"] += 1
            elif len(papers) > 1:
                counters["reference_targets_ambiguous"] += 1
            else:
                (cited,) = papers
                if cited == paper_id:
                    counters["reference_targets_self"] += 1
                else:
                    add_edge("CITES", paper_id, cited, "observed", [info["evidence"].id], METHOD_VERSION)

    # ---- taxonomy and phrase-baseline topics (R5, R6)
    taxonomy_bytes = taxonomy_path.read_bytes()
    taxonomy_hash = hashlib.sha256(taxonomy_bytes).hexdigest()
    retrieved = datetime.now(timezone.utc).isoformat()
    for topic in taxonomy["parents"] + taxonomy["leaves"]:
        level = "leaf" if "parent_id" in topic else "parent"
        nodes[topic["id"]] = Node(id=topic["id"], label="Topic", name=topic["name"], properties={
            "level": level, "taxonomy_version": taxonomy["version"], "definition": topic.get("definition", "Parent grouping"),
            "taxonomy_status": taxonomy["status"]})
        if level == "leaf":
            record = EvidenceRecord(
                id="evidence:taxonomy:" + _sha(taxonomy_hash, topic["id"])[:24], kind="curated_taxonomy",
                source_url=TAXONOMY_SOURCE_URL, retrieved_at=retrieved, raw_sha256=taxonomy_hash,
                source_locator=f"{taxonomy_path}#leaves[id={topic['id']}]")
            evidence[record.id] = record
            add_edge("SUBTOPIC_OF", topic["id"], topic["parent_id"], "curated_taxonomy", [record.id], taxonomy["version"])
    topic_decisions = Counter()
    for row in rows:
        paper_id = row["paper_id"]
        oa = row["openalex"] if row["match"]["status"] == "matched" else None
        abstract = (oa or {}).get("abstract")
        text = row["roster"]["title"] + "\n" + (abstract or "")
        predictions, decision = predict(text, taxonomy)
        topic_decisions[decision] += 1
        nodes[paper_id].properties["topic_text"] = "title_and_abstract" if abstract else "title_only"
        counters["papers_with_abstract"] += bool(abstract)
        base = evidence[_work_evidence(row).id] if oa else evidence[_roster_evidence(row).id]
        for prediction in predictions:
            relation_id = edge_id("HAS_TOPIC", paper_id, prediction["topic_id"])
            record = EvidenceRecord(
                id="evidence:topic:" + relation_id.removeprefix("edge:"), kind="inferred_topic", source_url=base.source_url,
                retrieved_at=base.retrieved_at, raw_sha256=base.raw_sha256,
                source_locator=f"{base.source_locator};title+abstract[{prediction['start']}:{prediction['end']}]",
                excerpt=prediction["excerpt"])
            evidence[record.id] = record
            add_edge("HAS_TOPIC", paper_id, prediction["topic_id"], "inferred_topic", [record.id], TOPIC_METHOD,
                     {"evaluation_status": "uncalibrated_baseline"})
        counters["papers_topic_labeled"] += bool(predictions)

    graph = GraphArtifact(
        graph_version=graph_version, is_synthetic=False, nodes=sorted(nodes.values(), key=lambda n: n.id),
        edges=sorted(edges.values(), key=lambda e: e.edge_id), evidence=sorted(evidence.values(), key=lambda e: e.id),
        affiliation_observations=sorted(observations, key=lambda o: o.id))
    researcher_min = quality["derived"]["researcher_topic_min_distinct_papers"]
    organization_min = quality["derived"]["organization_topic_min_distinct_papers"]
    graph = materialize(graph, researcher_min, organization_min)
    errors = validate_graph(graph, max_topic_labels=quality["topics"]["max_labels_per_paper"], require_derived=True,
                            researcher_min=researcher_min, organization_min=organization_min)
    if errors:
        raise ValueError("release graph failed structural validation: " + "; ".join(errors[:5]))

    counts = graph_counts(graph)
    size_targets = quality["size"]
    domain_nodes = sum(counts["nodes_by_label"].values())
    size_gates = {
        "domain_nodes": {"status": "passed" if domain_nodes >= size_targets["min_domain_nodes"] else "failed",
                         "observed": domain_nodes, "minimum": size_targets["min_domain_nodes"]},
        "resolved_core_researchers": {
            "status": "passed" if counts["resolved_core_researchers"] >= size_targets["min_resolved_core_researchers"] else "failed",
            "observed": counts["resolved_core_researchers"], "minimum": size_targets["min_resolved_core_researchers"]},
        "unique_core_factual_edges": {
            "status": "passed" if counts["unique_core_factual_edges"] >= size_targets["min_unique_factual_edges"] else "failed",
            "observed": counts["unique_core_factual_edges"], "minimum": size_targets["min_unique_factual_edges"]},
        "all_relation_types_present": {
            "status": "passed" if len(counts["edges_by_relation"]) == size_targets["required_relation_types"] else "failed",
            "observed": len(counts["edges_by_relation"]), "required": size_targets["required_relation_types"]},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_bytes(output_dir / "graph.json", (graph.model_dump_json() + "\n").encode("utf-8"))
    write_bytes(output_dir / "review-queue.jsonl",
                "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in review).encode("utf-8"))
    summary = {
        "stage": "release-graph", "method_version": METHOD_VERSION, "topic_method": TOPIC_METHOD,
        "graph_version": graph_version, "inputs_sha256": inputs,
        "graph_sha256": hashlib.sha256((output_dir / "graph.json").read_bytes()).hexdigest(),
        "counts": json.loads(json.dumps(counts, default=str)),
        "size_gates": size_gates,
        "papers": len(accepted_papers) + counters["papers_unmatched"],
        "coverage": {
            "papers_with_abstract": counters["papers_with_abstract"],
            "author_positions": counters["author_positions"],
            "author_positions_accepted": counters["author_positions_accepted"],
            "author_positions_withheld": counters["author_positions_withheld"],
            "author_positions_withheld_by_reason": {k.removeprefix("author_positions_withheld_"): v for k, v in sorted(counters.items())
                                                    if k.startswith("author_positions_withheld_")},
            "papers_all_authorships_withheld": counters["papers_all_authorships_withheld"],
            "accepted_authorships_with_institution": counters["accepted_authorships_with_institution"],
            "papers_topic_labeled": counters["papers_topic_labeled"],
        },
        "name_matching": {"initials_tolerant": allow_initials, "exact": counters["author_positions_accepted"] - counters["author_positions_initials_match"],
                          "initials": counters["author_positions_initials_match"]},
        "citations": {key: counters[key] for key in ("reference_targets", "reference_targets_out_of_scope",
                                                    "reference_targets_ambiguous", "reference_targets_self")},
        "review_queue": dict(sorted(Counter(item["kind"] for item in review).items())),
        "topic_decisions": dict(sorted(topic_decisions.items())),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    write_bytes(output_dir / "summary.json", (json.dumps(summary, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    write_json(summary_path, summary)
    return summary
