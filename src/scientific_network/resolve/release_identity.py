"""Conservative full-source identity correction carrying frozen predictions forward.

ORCID evidence is syntactically complete and checksum-valid. Missing/null fields
are absence of evidence; any nonempty malformed value (or wrong container type)
is quarantined globally, never silently ignored as if it proved no conflict.
No names, current author profiles, model inference, or source reacquisition are used.
"""

from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from scientific_network.collect.storage import read_config, read_jsonl, write_bytes, write_json, write_jsonl
from scientific_network.contracts import GraphArtifact
from scientific_network.graph.materialize import materialize
from scientific_network.graph.validate import graph_counts, validate_graph
from scientific_network.resolve.release import short_id
from scientific_network.resolve.release_taxonomy import validate_taxonomy

CORRECTION_METHOD = "release-observed-orcid-identity-correction-v1"
ORCID_FULL = re.compile(r"(?:https?://orcid\.org/)?(\d{4}-\d{4}-\d{4}-\d{3}[\dXx])/?", re.IGNORECASE)
POLICIES = {
    "identity": "union checksum-valid singular and observed ORCIDs across all matched works; withhold multiple values globally",
    "malformed": "withhold globally on nonempty malformed values or wrong containers; missing/null is allowed",
    "unsupported_organizations": "remove organizations without surviving affiliation observations",
    "paper_metadata": "preserve all original paper properties; add identity_correction:all_authorships_withheld only when a newly authorless paper lacks a reason",
    "predictions": "preserve frozen HAS_TOPIC, taxonomy and all non-derived evidence exactly; no inference",
}


def valid_orcid(value) -> str | None:
    """Recognize a whole bare/ORCID URL identifier with ISO 7064 MOD 11-2 check digit."""
    if not isinstance(value, str):
        return None
    match = ORCID_FULL.fullmatch(value.strip())
    if not match:
        return None
    identifier = match[1].upper()
    digits, total = identifier.replace("-", ""), 0
    for digit in digits[:-1]:
        total = (total + int(digit)) * 2
    check = (12 - total % 11) % 11
    return identifier if digits[-1] == ("X" if check == 10 else str(check)) else None


def collect_identity_evidence(rows: list[dict]) -> dict:
    """Collect exact retained-source field provenance, without inspecting graph/sample membership.

    ``source_locator`` is the raw request work locator; ``field_locator`` names
    the exact field in immutable works.jsonl. Retained observed_orcids may combine
    source observations, so no invented raw-response per-value locator is claimed.
    """
    values, records, malformed = defaultdict(set), defaultdict(list), set()
    authors = set()
    for row_index, row in enumerate(rows):
        if row["match"]["status"] != "matched":
            continue
        work, paper = row["openalex"], row["paper_id"]
        source = work["source"]
        for position, authorship in enumerate(work["authorships"]):
            author = authorship.get("author") or {}
            identifier = short_id(author.get("id"))
            if not identifier:
                continue
            authors.add(identifier)
            candidates = [("orcid", author.get("orcid"), False)]
            observed = author.get("observed_orcids")
            if observed is not None:
                if isinstance(observed, list):
                    candidates.extend((f"observed_orcids[{index}]", value, True) for index, value in enumerate(observed))
                else:
                    candidates.append(("observed_orcids", observed, True))
            for field, raw, array_value in candidates:
                # Empty singular strings are absence; array entries must be actual valid IDs.
                missing = not array_value and (raw is None or (isinstance(raw, str) and not raw.strip()))
                if missing:
                    continue
                normalized = valid_orcid(raw) if field != "observed_orcids" else None
                if normalized:
                    values[identifier].add(normalized)
                else:
                    malformed.add(identifier)
                records[identifier].append({
                    "paper_id": paper, "openalex_work_id": work["id"], "byline_position": position + 1,
                    "field": field, "raw_value": raw, "normalized_orcid": normalized,
                    "status": "valid" if normalized else "malformed", "request_id": source["request_id"],
                    "raw_sha256": source["raw_sha256"], "retrieved_at": source["retrieved_at"],
                    "source_url": source.get("url", "https://api.openalex.org/works"),
                    "source_locator": f"openalex-request:{source['request_id']}#{source['locator']}",
                    "field_locator": f"works.jsonl:line={row_index + 1}#/openalex/authorships/{position}/author/{field}",
                    "source_depth": "retained_immutable_work_fields; raw request hash and work locator preserved",
                })
    conflicts = {identifier for identifier, found in values.items() if len(found) > 1}
    withheld = {identifier: ("author_id_conflicting_orcids" if identifier in conflicts else "author_id_malformed_orcid")
                for identifier in sorted(conflicts | malformed)}
    review = [{"kind": reason, "author_id": identifier, "orcids": sorted(values[identifier]),
               "has_malformed_evidence": identifier in malformed, "source_observations": records[identifier]}
              for identifier, reason in withheld.items()]
    return {"orcids": values, "withheld": withheld, "review": review,
            "counts": {"matched_author_ids": len(authors), "conflicting_author_ids": len(conflicts),
                       "malformed_author_ids": len(malformed), "withheld_author_ids": len(withheld),
                       "source_orcid_observations": sum(map(len, records.values()))}}


def _digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _dump(item, *, edge=False):
    return item.model_dump(mode="json", exclude={"graph_version"} if edge else set())


def identity_invariants(old: GraphArtifact, new: GraphArtifact) -> dict:
    """Prove exact canonical equivalence of every protected claim and source record."""
    original_papers = {n.id: n for n in old.nodes if n.label == "Paper"}
    authored_papers = {e.target_id for e in new.edges if e.relation == "AUTHORED"}

    def protected_node(node):
        content = _dump(node)
        if (node.label == "Paper" and node.id not in authored_papers
                and "unresolved_author_reason" not in original_papers[node.id].properties
                and content["properties"].get("unresolved_author_reason") == "identity_correction:all_authorships_withheld"):
            content["properties"].pop("unresolved_author_reason")
        return content

    def groups(graph):
        return {
            "paper_venue_topic_nodes": [protected_node(n) for n in sorted(graph.nodes, key=lambda n: n.id)
                                         if n.label in {"Paper", "Venue", "Topic"}],
            "publication_citation_topic_taxonomy_edges": [_dump(e, edge=True) for e in sorted(graph.edges, key=lambda e: e.edge_id)
                if e.relation in {"PUBLISHED_IN", "CITES", "HAS_TOPIC", "SUBTOPIC_OF"}],
            "non_derived_evidence": [_dump(e) for e in sorted(graph.evidence, key=lambda e: e.id) if e.kind != "derived"],
        }
    before, after = groups(old), groups(new)
    proof = {}
    for key in before:
        a, b = _digest(before[key]), _digest(after[key])
        if a != b:
            raise ValueError(f"identity correction changed protected claims: {key}")
        proof[key] = {"before_sha256": a, "after_sha256": b, "equal": True}
    if old.graph_version == new.graph_version or any(e.graph_version != new.graph_version for e in new.edges):
        raise ValueError("identity correction must restamp every edge with a new graph version")
    return proof


def _changes(old, new, collection, key, *, edge=False):
    before, after = {getattr(i, key): i for i in old}, {getattr(i, key): i for i in new}
    result = []
    for identifier in sorted(before.keys() | after.keys()):
        a, b = before.get(identifier), after.get(identifier)
        if a is not None and b is not None and _dump(a, edge=edge) == _dump(b, edge=edge):
            continue
        result.append({"collection": collection, "id": identifier,
                       "change": "added" if a is None else "removed" if b is None else "changed",
                       "before": _dump(a, edge=edge) if a is not None else None,
                       "after": _dump(b, edge=edge) if b is not None else None})
    return result


def _size_gates(counts, quality):
    targets = quality["size"]
    values = {"domain_nodes": (sum(counts["nodes_by_label"].values()), targets["min_domain_nodes"]),
              "resolved_core_researchers": (counts["resolved_core_researchers"], targets["min_resolved_core_researchers"]),
              "unique_core_factual_edges": (counts["unique_core_factual_edges"], targets["min_unique_factual_edges"]),
              "all_relation_types_present": (len(counts["edges_by_relation"]), targets["required_relation_types"])}
    return {key: {"observed": observed, "minimum": minimum,
                  "status": "passed" if observed >= minimum else "failed"}
            for key, (observed, minimum) in values.items()}


def _bound_hash(field, actual, label):
    if field != actual:
        raise ValueError(f"{label} differs from frozen input")


def correct_release_identity(works_path: Path, input_path: Path, taxonomy_path: Path, quality_path: Path,
                             source_summary_path: Path, source_freeze_path: Path, protocol_path: Path,
                             output_dir: Path, summary_path: Path, freeze_path: Path) -> dict:
    """Write a deterministic new graph, exhaustive change ledger and content freeze.

    Every output path must be unused, including dangling symlinks. Changes JSONL
    excludes universal graph_version stamping; its manifest explicitly accounts
    for that stamp across every surviving edge. Source graph/files remain immutable.
    """
    destinations = [output_dir, summary_path, freeze_path]
    if any(p.exists() or p.is_symlink() for p in destinations):
        raise ValueError("correction outputs must use unused versioned paths")
    if len({p.resolve() for p in destinations}) != len(destinations):
        raise ValueError("correction output paths must be distinct")
    if summary_path.is_relative_to(output_dir) or freeze_path.is_relative_to(output_dir):
        raise ValueError("summary and content freeze must be outside graph output directory")
    sources = {"works": works_path, "source_graph": input_path, "taxonomy": taxonomy_path,
               "quality": quality_path, "source_summary": source_summary_path,
               "source_freeze": source_freeze_path, "correction_protocol": protocol_path}
    hashes = {key: sha256(path.read_bytes()).hexdigest() for key, path in sources.items()}
    source_freeze = json.loads(source_freeze_path.read_bytes())
    summary = json.loads(source_summary_path.read_bytes())
    _bound_hash(source_freeze["graph_sha256"], hashes["source_graph"], "source graph")
    _bound_hash(summary["graph_sha256"], hashes["source_graph"], "source summary graph")
    _bound_hash(source_freeze["source_inputs"]["works"]["sha256"], hashes["works"], "works")
    if source_freeze.get("correction_summary"):
        _bound_hash(source_freeze["correction_summary"]["sha256"], hashes["source_summary"], "source summary")
    for path, key in ((taxonomy_path, "taxonomy"), (quality_path, "quality")):
        _bound_hash(source_freeze["config_hashes"].get(str(path)), hashes[key], key)
    old = GraphArtifact.model_validate_json(input_path.read_bytes())
    if old.is_synthetic or old.graph_version != source_freeze["graph_version"] or old.graph_version != summary["graph_version"]:
        raise ValueError("correction requires the frozen real release graph")
    quality = read_config(quality_path)
    validate_args = dict(require_derived=True, max_topic_labels=quality["topics"]["max_labels_per_paper"],
                         researcher_min=quality["derived"]["researcher_topic_min_distinct_papers"],
                         organization_min=quality["derived"]["organization_topic_min_distinct_papers"])
    errors = validate_taxonomy(old, taxonomy_path) + validate_graph(old, **validate_args)
    if errors:
        raise ValueError("source graph validation failed: " + "; ".join(errors[:10]))
    rows = read_jsonl(works_path)
    papers = {n.id: n for n in old.nodes if n.label == "Paper"}
    if len(rows) != len(papers) or {r["paper_id"] for r in rows} != set(papers):
        raise ValueError("immutable works must contain each frozen graph paper exactly once")
    if any(papers[r["paper_id"]].properties["official_author_count"] != len(r["roster"]["authors"]) for r in rows):
        raise ValueError("official byline counts differ from immutable works")
    identity = collect_identity_evidence(rows)
    withheld = {"researcher:openalex:" + identifier for identifier in identity["withheld"]}
    version = "release-" + _digest([CORRECTION_METHOD, hashes, POLICIES])[:12]
    observations = [o for o in old.affiliation_observations if o.researcher_id not in withheld]
    supported_orgs = {o.organization_id for o in observations}
    removed_orgs = {n.id for n in old.nodes if n.label == "Organization" and n.id not in supported_orgs}
    graph = old.model_copy(update={
        "graph_version": version,
        "nodes": [n for n in old.nodes if n.id not in withheld | removed_orgs],
        "affiliation_observations": observations,
        "edges": [e.model_copy(update={"graph_version": version}) for e in old.edges
                  if e.evidence_kind != "derived" and e.source_id not in withheld | removed_orgs and e.target_id not in withheld | removed_orgs],
        "evidence": [e for e in old.evidence if e.kind != "derived"],
    })
    # R2 is aggregated over surviving triples. All observations of a withheld ID
    # are removed together; surviving R2 strings/evidence therefore stay exact.
    support = defaultdict(list)
    for observation in observations:
        support[observation.researcher_id, observation.organization_id].append(observation)
    for edge in graph.edges:
        if edge.relation == "AFFILIATED_WITH":
            group = support.pop((edge.source_id, edge.target_id), [])
            if not group or edge.properties.get("support_paper_count") != len({o.paper_id for o in group}):
                raise ValueError("surviving affiliation aggregate disagrees with observations")
            if set(edge.evidence_ids) != {ev for observation in group for ev in observation.evidence_ids}:
                raise ValueError("surviving affiliation evidence disagrees with observations")
    if support:
        raise ValueError("surviving affiliation observation has no aggregate")
    remaining_authored_papers = {e.target_id for e in graph.edges if e.relation == "AUTHORED"}
    graph.nodes = [n.model_copy(update={"properties": {**n.properties,
        "unresolved_author_reason": "identity_correction:all_authorships_withheld"}})
        if n.label == "Paper" and n.id not in remaining_authored_papers and not n.properties.get("unresolved_author_reason")
        else n for n in graph.nodes]
    graph = materialize(graph, validate_args["researcher_min"], validate_args["organization_min"])
    invariants = identity_invariants(old, graph)
    errors = validate_taxonomy(graph, taxonomy_path) + validate_graph(graph, **validate_args)
    if errors:
        raise ValueError("corrected graph validation failed: " + "; ".join(errors[:10]))
    changes = []
    for collection, key, edge in (("nodes", "id", False), ("edges", "edge_id", True),
                                  ("evidence", "id", False), ("affiliation_observations", "id", False)):
        changes.extend(_changes(getattr(old, collection), getattr(graph, collection), collection, key, edge=edge))
    if any(c["change"] == "added" and c["collection"] != "evidence" for c in changes):
        raise ValueError("identity withholding unexpectedly added a graph claim")
    removed_authorships = [e for e in old.edges if e.relation == "AUTHORED" and e.source_id in withheld]
    all_authorships = [e for e in graph.edges if e.relation == "AUTHORED"]
    institutions = {(o.researcher_id, o.paper_id) for o in observations}
    matched_rows = [r for r in rows if r["match"]["status"] == "matched"]
    total_positions = sum(len(r["roster"]["authors"]) for r in matched_rows)
    accepted_papers = {e.target_id for e in all_authorships}
    removed_by_reason = Counter(identity["withheld"][e.source_id.removeprefix("researcher:openalex:")]
                                for e in removed_authorships)
    source_coverage = summary.get("coverage", {})
    source_reasons = source_coverage.get("author_positions_withheld_by_reason")
    historical_withheld = total_positions - len(all_authorships) - len(removed_authorships)
    if source_reasons is None:
        # Frozen embedding summaries omit the builder's reason table. Never invent
        # detailed historical reasons from paper metadata or absent queue records.
        source_reasons = {"historical_withheld_reason_not_carried_in_source_summary": historical_withheld} if historical_withheld else {}
    if sum(source_reasons.values()) != historical_withheld:
        raise ValueError("historical withheld-reason totals disagree with frozen graph")
    reasons = Counter(source_reasons) + removed_by_reason
    accepted_initials = sum(e.properties.get("name_match") == "initials" for e in all_authorships)
    coverage = {**source_coverage,
        "official_author_positions_all_roster_papers": sum(len(r["roster"]["authors"]) for r in rows),
        "author_positions": total_positions, "author_positions_accepted": len(all_authorships),
        "author_positions_withheld": total_positions - len(all_authorships),
        "author_positions_withheld_by_reason": dict(sorted(reasons.items())),
        "accepted_authorships_with_institution": len(institutions),
        "author_paper_affiliation_coverage": len(institutions) / total_positions if total_positions else 0,
        "papers_all_authorships_withheld": sum(r["paper_id"] not in accepted_papers for r in matched_rows),
        "papers_without_accepted_authorship": len(papers.keys() - accepted_papers),
        "identity_correction_removed_authorships": len(removed_authorships),
        "paper_unresolved_reason_policy": POLICIES["paper_metadata"],
    }
    counts = graph_counts(graph)
    output_dir.mkdir(parents=True)
    graph_path, changes_path = output_dir / "graph.json", output_dir / "changes.jsonl"
    review_path, manifest_path = output_dir / "review-queue.jsonl", output_dir / "change-manifest.json"
    write_bytes(graph_path, (graph.model_dump_json() + "\n").encode())
    write_jsonl(changes_path, changes)
    write_jsonl(review_path, identity["review"])
    changed_counts = Counter((c["collection"], c["change"]) for c in changes)
    manifest = {
        "method_version": CORRECTION_METHOD, "source_graph_version": old.graph_version, "graph_version": version,
        "policies": POLICIES, "invariants": invariants,
        "before_counts": graph_counts(old), "after_counts": counts,
        "changes": {collection: {kind: changed_counts[collection, kind] for kind in ("removed", "changed", "added")}
                    for collection in ("nodes", "edges", "evidence", "affiliation_observations")},
        "change_ledger": {"path": str(changes_path), "sha256": sha256(changes_path.read_bytes()).hexdigest(),
                          "rows": len(changes), "format": "full before/after records, edges exclude graph_version only"},
        "graph_version_restamp": {"before": old.graph_version, "after": version, "edge_count": len(graph.edges),
                                  "surviving_edge_ids_sha256": _digest(sorted(e.edge_id for e in graph.edges)),
                                  "rule": "every surviving edge is restamped; no other unstated changes"},
        "removed_researcher_ids": sorted(n.id for n in old.nodes if n.label == "Researcher" and n.id in withheld),
        "removed_unsupported_organization_ids": sorted(removed_orgs),
        "source_identity_counts": identity["counts"],
    }
    write_json(manifest_path, manifest)
    result = {**summary, "stage": "release-identity-correction", "method_version": CORRECTION_METHOD,
              "supersedes_graph_version": old.graph_version, "graph_version": version,
              "graph_sha256": sha256(graph_path.read_bytes()).hexdigest(), "counts": counts,
              "topic_classifier_method_version": summary.get("topic_classifier_method_version", summary.get("topic_method", summary["method_version"])),
              "name_matching": {"initials_tolerant": summary.get("name_matching", {}).get("initials_tolerant"),
                                "exact": len(all_authorships) - accepted_initials, "initials": accepted_initials},
              "coverage": coverage, "size_gates": _size_gates(counts, quality),
              "identity": identity["counts"], "policies": POLICIES, "preservation": invariants,
              "correction_inputs": {key: {"path": str(sources[key]), "sha256": digest} for key, digest in hashes.items()},
              "change_manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path.read_bytes()).hexdigest()},
              "review_queue": dict(Counter(r["kind"] for r in identity["review"])),
              "structural_validation": "passed", "taxonomy_validation": "passed",
              "semantic_accuracy": "not_measured_for_corrected_graph",
              "computation": "full-source global identity withholding; R7-R10 recomputed; frozen predictions/evidence copied without inference"}
    # Older coverage remains useful for topics; historical phase/accuracy claims do not.
    result.pop("created_at", None)
    write_json(summary_path, result)
    write_json(output_dir / "summary.json", result)
    freeze = {"status": "frozen", "freeze_method_version": CORRECTION_METHOD,
              "frozen_at": datetime.now(ZoneInfo("Asia/Bangkok")).isoformat(),
              "supersedes": {"path": str(source_freeze_path), "sha256": hashes["source_freeze"]},
              "graph_path": str(graph_path), "graph_version": version, "graph_sha256": result["graph_sha256"],
              "source_inputs": result["correction_inputs"],
              "config_hashes": source_freeze["config_hashes"],
              "method_versions": {**source_freeze.get("method_versions", {}), "identity_correction": CORRECTION_METHOD},
              "correction_summary": {"path": str(summary_path), "sha256": sha256(summary_path.read_bytes()).hexdigest()},
              "change_manifest": result["change_manifest"],
              "preservation": invariants, "audit_status": "not_started; new prospective audit required",
              "graph_mutation_policy": "immutable; new correction requires separate authorization/version"}
    write_json(freeze_path, freeze)
    return result
