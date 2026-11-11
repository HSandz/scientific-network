"""Offline v5 census of immutable release inputs; no collection or semantic gold labels.

Run ``python -m scientific_network.quality.identity_audit --help``. Every output
directory must be unused. Record-level diagnostics stay in ignored local storage.
"""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

import networkx as nx

from scientific_network.collect.acquire import name_tokens
from scientific_network.collect.openalex_release import normalize_doi, title_similarity
from scientific_network.collect.storage import read_jsonl, write_json, write_jsonl
from scientific_network.contracts import GraphArtifact
from scientific_network.graph.validate import graph_counts, validate_graph
from scientific_network.resolve.release import authorship_institutions, name_match, short_id
from scientific_network.resolve.release_identity import collect_identity_evidence, valid_orcid

METHOD = "quality-identity-census-v5.1"


def file_hash(path):
    with Path(path).open("rb") as stream:
        from hashlib import file_digest
        return file_digest(stream, "sha256").hexdigest()


def unused(*paths):
    resolved = [p.resolve() for p in paths]
    if len(set(resolved)) != len(paths) or any(p.exists() or p.is_symlink() for p in paths):
        raise ValueError("outputs must be distinct unused versioned paths (including symlinks)")


def network_summary(graph):
    net = nx.Graph()
    net.add_nodes_from(n.id for n in graph.nodes if n.label == "Researcher")
    net.add_edges_from((e.source_id, e.target_id) for e in graph.edges if e.relation == "COAUTHORED_WITH")
    components = sorted((len(c) for c in nx.connected_components(net)), reverse=True)
    return {"researchers": len(net), "coauthorship_pairs": net.number_of_edges(),
            "components": len(components), "isolates": len(list(nx.isolates(net))),
            "largest_component": components[0] if components else 0,
            "top_degree": [{"id": n, "degree": d} for n, d in sorted(net.degree, key=lambda x: (-x[1], x[0]))[:20]]}


def census(rows, graph, cache_dir=None):
    identity = collect_identity_evidence(rows)
    withheld = identity["withheld"]
    accepted = {(e.target_id, e.properties["byline_position"]): e.source_id
                for e in graph.edges if e.relation == "AUTHORED"}
    affiliated = {(o.researcher_id, o.paper_id) for o in graph.affiliation_observations}
    strata, total = defaultdict(Counter), Counter()
    details, source_checks = [], []
    doi_papers, work_papers, institution_records = defaultdict(set), defaultdict(set), defaultdict(set)
    author_names, author_raw_orcids, author_sets = defaultdict(set), defaultdict(set), defaultdict(set)
    author_affiliations, conflict_neighbors = defaultdict(set), defaultdict(set)
    name_providers, orcid_providers = defaultdict(set), defaultdict(set)
    conflict_positions, conflicting_singular = Counter(), defaultdict(set)
    raw_cache = {}
    legacy_reasons = Counter()
    leaked_after_shadow, trigger = [], None
    for line, row in enumerate(rows, 1):
        counts = strata[f"{row['venue_id']}:{row['year']}"]
        def count(key, amount=1):
            counts[key] += amount
            total[key] += amount
        paper = row["paper_id"]
        doi_papers[normalize_doi(row["doi"])].add(paper)
        count("papers"); count("official_positions", len(row["roster"]["authors"]))
        count("work_status:" + row["match"]["status"])
        for reason in row["match"].get("reasons", []):
            count("work_rejection:" + reason)
        for flag in row["match"].get("flags", []):
            count("work_flag:" + flag)
        if row["match"]["status"] != "matched":
            continue
        oa, names = row["openalex"], row["roster"]["authors"]
        source = oa["source"]
        work_papers[short_id(oa["id"])].add(paper)
        for alternate in oa.get("alternates", []):
            work_papers[short_id(alternate["id"])].add(paper)
        count("works_with_alternates", bool(oa.get("alternates")))
        count("missing_abstract", not bool(oa.get("abstract")))
        count("doi_disagreement", normalize_doi(row["doi"]) != normalize_doi(oa.get("doi")))
        count("positions_on_doi_disagreement_works", len(names) if normalize_doi(row["doi"]) != normalize_doi(oa.get("doi")) else 0)
        count("title_below_threshold", title_similarity(names and row["roster"]["title"], oa.get("title")) < .9)
        count("title_not_exact", title_similarity(row["roster"]["title"], oa.get("title")) < 1)
        count("author_count_disagreement", len(names) != len(oa["authorships"]))
        count("publication_year_disagreement", row["year"] != oa.get("publication_year"))
        count("reference_occurrences", len(oa.get("referenced_works", [])))
        count("duplicate_reference_occurrences", len(oa.get("referenced_works", []))-len(set(oa.get("referenced_works", []))))
        count("works_without_references", not bool(oa.get("referenced_works")))
        if cache_dir:
            digest = source["raw_sha256"]
            if digest not in raw_cache:
                path = cache_dir / "objects" / digest
                body = path.read_bytes()
                if sha256(body).hexdigest() != digest:
                    raise ValueError("cached source hash mismatch: " + digest)
                raw_cache[digest] = json.loads(body)
            raw = raw_cache[digest]
            match = re.fullmatch(r"results\[(\d+)\](?:@page\d+)?", source["locator"])
            raw = raw["results"][int(match[1])] if match else raw
            check = {"paper_id": paper, "raw_sha256": digest, "source_locator": source["locator"],
                     "work_id_equal": raw.get("id") == oa["id"],
                     "authorships_equal": raw.get("authorships", []) == oa["authorships"],
                     "references_equal": raw.get("referenced_works", []) == oa["referenced_works"]}
            source_checks.append(check)
            if not all(check[k] for k in ("work_id_equal", "authorships_equal", "references_equal")):
                raise ValueError("retained work differs from cached source: " + paper)
        ids = [short_id((a.get("author") or {}).get("id")) for a in oa["authorships"]]
        duplicate_ids = {a for a, n in Counter(ids).items() if a and n > 1}
        bad_names = sum(name_match(n, a, False) is None for n, a in zip(names, oa["authorships"]))
        # Exact historical v1.1 byline rules, before the observed-ORCID correction.
        usable_ids = [aid for n, a, aid in zip(names, oa["authorships"], ids)
                      if aid and name_match(n, a, False)]
        whole_reason = ("multiple_incompatible_positions" if bad_names > 1 else
                        "author_id_repeated_in_paper" if len(usable_ids) != len(set(usable_ids)) else None)
        count("papers_multiple_name_mismatches", bad_names > 1)
        count("papers_duplicate_provider_positions", bool(duplicate_ids))
        # Detect where current v1.2 loses its global lookup. Earlier conflicts do
        # not count as leakage; repeated later whole-paper rejection resets it too.
        current_usable = [aid for n, a, aid in zip(names, oa["authorships"], ids)
                          if aid and aid not in withheld and name_match(n, a, False)]
        triggers = bad_names > 1 or len(current_usable) != len(set(current_usable))
        if trigger:
            leaked_after_shadow.extend((paper, i+1, aid) for i, (n, a, aid) in
                                      enumerate(zip(names, oa["authorships"], ids))
                                      if aid in withheld and name_match(n, a, False))
        if triggers and trigger is None:
            trigger = paper
        per_paper = []
        for i, name in enumerate(names):
            a = oa["authorships"][i] if i < len(oa["authorships"]) else {}
            author = a.get("author") or {}
            aid = short_id(author.get("id"))
            kind = name_match(name, a, False)
            count("matched_positions")
            is_accepted = (paper, i+1) in accepted
            count("accepted_positions", is_accepted); count("withheld_positions", not is_accepted)
            count("accepted_affiliated_positions", (accepted.get((paper, i+1)), paper) in affiliated)
            count("missing_author_id", aid is None)
            count("name_mismatch", not kind)
            count("raw_name_missing", not bool(a.get("raw_author_name")))
            count("canonical_name_only_match", bool(kind) and not name_match(name, {"raw_author_name": a.get("raw_author_name")}, False))
            count("duplicate_provider_positions", aid in duplicate_ids)
            count("global_conflict_positions", aid in withheld)
            count("raw_orcid_present", bool(a.get("raw_orcid")))
            count("raw_orcid_valid", bool(valid_orcid(a.get("raw_orcid"))))
            if aid:
                author_names[aid].add(name)
                author_sets[aid].add(tuple(sorted(v for v in (valid_orcid(x) for x in author.get("observed_orcids") or []) if v)))
                if valid_orcid(a.get("raw_orcid")):
                    author_raw_orcids[aid].add(valid_orcid(a["raw_orcid"]))
                if valid_orcid(author.get("orcid")):
                    conflicting_singular[aid].add(valid_orcid(author["orcid"]))
                name_providers[tuple(name_tokens(name))].add(aid)
                for v in identity["orcids"].get(aid, []):
                    orcid_providers[v].add(aid)
            if aid in withheld:
                conflict_positions[aid] += 1
                conflict_neighbors[aid].update(x for x in ids if x and x != aid)
                count("conflict_positions_with_raw_orcid", bool(valid_orcid(a.get("raw_orcid"))))
            reason = ("name_incompatible" if not kind else "no_author_id" if not aid else
                      whole_reason or withheld.get(aid) or "historical_accepted")
            if not is_accepted:
                legacy_reasons[reason] += 1
                count("absent_reason:" + reason)
            institutions = authorship_institutions(a)
            if aid:
                author_affiliations[aid].add(tuple(sorted(x["id"] for x in institutions)))
            per_paper.append((i, institutions))
            count("positions_missing_institutions", not institutions)
            count("institution_assignments", len(institutions))
            count("institution_assignments_missing_ror", sum(not x.get("ror") for x in institutions))
            count("institution_assignments_without_raw_strings", sum(not x["raw_strings"] for x in institutions))
            count("institution_assignments_fallback_mapping", sum(x["raw_string_mapping"] == "authorship_level" for x in institutions))
            count("multi_institution_positions", len(institutions) > 1)
            for inst in institutions:
                institution_records[inst["id"]].add(tuple(inst.get(k) for k in ("name", "ror", "country_code", "type")))
            details.append({"paper_id": paper, "venue_id": row["venue_id"], "year": row["year"],
                            "position": i+1, "author_id": aid, "accepted_v4": is_accepted,
                            "diagnostic_reason": reason, "global_withheld": aid in withheld,
                            "raw_orcid": valid_orcid(a.get("raw_orcid")),
                            "institution_ids": [x["id"] for x in institutions],
                            "works_locator": f"line={line}#/openalex/authorships/{i}",
                            "raw_sha256": source["raw_sha256"], "raw_locator": source["locator"]})
        accepted_insts = [frozenset(x["id"] for x in insts) for i, insts in per_paper if (paper, i+1) in accepted]
        if len(accepted_insts) >= 3 and len(set(accepted_insts)) == 1 and len(accepted_insts[0]) >= 2:
            count("copy_guard_papers_on_surviving_positions")
            count("copy_guard_positions_on_surviving_positions", len(accepted_insts))
    conflicts = set(withheld)
    conflicts_raw = {a for a in conflicts if author_raw_orcids[a]}
    evidence_ids = {e.id for e in graph.evidence}
    graph_source_hashes = {e.raw_sha256 for e in graph.evidence if e.raw_sha256}
    absent_source_hashes = sorted(h for h in graph_source_hashes if cache_dir and not (cache_dir / "objects" / h).exists())
    result = {"method_version": METHOD, "metrics": dict(sorted(total.items())),
              "by_venue_year": {k: dict(sorted(v.items())) for k, v in sorted(strata.items())},
              "duplicates": {"doi_groups": {k: sorted(v) for k, v in doi_papers.items() if len(v)>1},
                             "openalex_work_groups": {k: sorted(v) for k, v in work_papers.items() if len(v)>1}},
              "identity": {**identity["counts"],
                           "conflict_positions": sum(conflict_positions.values()),
                           "conflicting_ids_with_paper_raw_orcid": len(conflicts_raw),
                           "conflicting_ids_with_multiple_paper_raw_orcids": sum(len(author_raw_orcids[a])>1 for a in conflicts),
                           "conflicting_ids_with_multiple_singular_orcids": sum(len(conflicting_singular[a])>1 for a in conflicts),
                           "conflicting_ids_with_identical_observed_sets_across_works": sum(len(author_sets[a])==1 for a in conflicts),
                           "multiple_provider_ids_per_normalized_name_groups": sum(len(v)>1 for v in name_providers.values()),
                           "orcids_shared_across_provider_ids": sum(len(v)>1 for v in orcid_providers.values()),
                           "provider_ids_with_incompatible_official_name_variants": sum(
                               len({tuple(name_tokens(n)) for n in ns}) > 1 for ns in author_names.values()),
                           "provider_ids_with_varying_affiliation_sets": sum(len(v)>1 for v in author_affiliations.values()),
                           "most_influential_withheld_source_ids": [
                               {"id": a, "source_positions": conflict_positions[a], "source_coauthor_provider_ids": len(conflict_neighbors[a])}
                               for a in sorted(conflicts, key=lambda a: (-len(conflict_neighbors[a]), a))[:20]],
                           "caution": "aggregated author-object observations are not paper-specific identity truth; name groups are inspection leads only"},
              "institutions": {"distinct_ids": len(institution_records),
                               "ids_with_inconsistent_name_ror_country_type": sum(len(v)>1 for v in institution_records.values())},
              "shadow_bug": {"first_trigger_paper": trigger,
                             "subsequent_name_compatible_conflict_positions_exposed": len(leaked_after_shadow),
                             "history": "v1.2 introduced dictionary/string reuse; v1.1 and frozen v4 correction did not use this state path"},
              "graph_counts": graph_counts(graph), "researcher_network": network_summary(graph),
              "structural_errors": validate_graph(graph, require_derived=True),
              "unresolved_domain_researchers": sum(n.label == "Researcher" and n.properties.get("resolution_status") != "resolved" for n in graph.nodes),
              "edges_with_missing_evidence_ids": sum(any(i not in evidence_ids for i in e.evidence_ids) for e in graph.edges),
              "source_check": {"matched_works_compared": len(source_checks), "raw_objects_verified": len(raw_cache),
                               "all_equal": all(c["authorships_equal"] and c["references_equal"] and c["work_id_equal"] for c in source_checks),
                               "non_openalex_graph_source_hashes": len(absent_source_hashes)},
              "semantic_metrics": {k: None for k in ("identity_pairwise_precision", "identity_pairwise_recall", "identity_pairwise_f1", "false_merges", "false_splits", "authorship_precision", "authorship_recall")},
              "evaluation_status": "no independent identity labels; descriptive source/coverage checks only"}
    return result, details, source_checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--works", type=Path, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--detail-dir", type=Path, required=True)
    args = parser.parse_args()
    unused(args.output_dir, args.detail_dir)
    hashes = {k: file_hash(getattr(args, k)) for k in ("works", "graph", "freeze")}
    freeze = json.loads(args.freeze.read_bytes())
    if hashes["works"] != freeze["source_inputs"]["works"]["sha256"] or hashes["graph"] != freeze["graph_sha256"]:
        raise ValueError("inputs do not match immutable freeze")
    graph = GraphArtifact.model_validate_json(args.graph.read_bytes())
    result, details, checks = census(read_jsonl(args.works), graph, args.cache_dir)
    result["inputs"] = {k: {"path": str(getattr(args,k)), "sha256": v} for k,v in hashes.items()}
    result["graph_version"] = graph.graph_version
    args.output_dir.mkdir(parents=True)
    args.detail_dir.mkdir(parents=True)
    write_jsonl(args.detail_dir / "positions.jsonl", details)
    write_jsonl(args.detail_dir / "source-checks.jsonl", checks)
    result["details"] = {p.name: {"path": str(p), "sha256": file_hash(p)} for p in sorted(args.detail_dir.iterdir())}
    write_json(args.output_dir / "baseline-audit.json", result)
    print(json.dumps({"output": str(args.output_dir), "metrics": result["metrics"], "identity": result["identity"], "shadow_bug": result["shadow_bug"]}, indent=2))


if __name__ == "__main__":
    main()
