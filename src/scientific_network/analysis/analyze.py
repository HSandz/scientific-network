"""Deterministic descriptive analysis for versioned graph artifacts.

Synthetic graphs are supported for protocol checks only. Real graphs require a
frozen analysis/evidence-sensitivity configuration; the quality-config size gates are
computed and recorded as passed or failed (D040), and a readiness receipt is optional.
This module does not produce source-backed business findings or certify semantic
quality.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

import networkx as nx
import yaml

from scientific_network.contracts import EvidenceKind, GraphArtifact, Relation
from scientific_network.graph.schema import RELATIONSHIPS
from scientific_network.graph.validate import graph_counts, validate_graph
from scientific_network.analysis.release_metrics import compute_release_metrics


METHOD_VERSION = "named-projection-analysis-v2"
REQUIRED_PROJECTIONS = {
    "researcher_collaboration",
    "organization_collaboration",
    "core_citations",
    "paper_topics",
    "organization_topics",
}


def _positive_int(value, name: str, *, allow_zero: bool = False) -> int:
    minimum = 0 if allow_zero else 1
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _load_config(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    config = yaml.safe_load(raw)
    if not isinstance(config, dict) or not isinstance(config.get("version"), str):
        raise ValueError("analysis configuration must be a versioned mapping")
    if config.get("status") not in {"proposed", "frozen"}:
        raise ValueError("analysis configuration status must be proposed or frozen")
    _positive_int(config.get("random_seed"), "random_seed", allow_zero=True)

    projections = config.get("projections")
    if not isinstance(projections, dict) or set(projections) != REQUIRED_PROJECTIONS:
        raise ValueError("analysis config must define exactly the five named projections")
    for name, spec in projections.items():
        if not isinstance(spec, dict):
            raise ValueError(f"projections.{name} must be a mapping")
        try:
            relation = Relation(spec.get("relation"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"projections.{name}.relation is not a graph predicate") from exc
        relationship = RELATIONSHIPS[relation]
        labels_value = spec.get("node_labels", spec.get("node_label"))
        if isinstance(labels_value, str):
            labels = [labels_value]
        elif isinstance(labels_value, list) and all(isinstance(value, str) for value in labels_value):
            labels = labels_value
        else:
            raise ValueError(f"projections.{name} requires node_label or node_labels")
        expected_labels = {relationship.source.value, relationship.target.value}
        if len(labels) != len(set(labels)) or set(labels) != expected_labels:
            raise ValueError(f"projections.{name} node labels do not match {relation.value} endpoints")
        if type(spec.get("directed")) is not bool:
            raise ValueError(f"projections.{name}.directed must be boolean")
        if "core_only" in spec and type(spec["core_only"]) is not bool:
            raise ValueError(f"projections.{name}.core_only must be boolean")
        paper_endpoints = relationship.source.value == "Paper" and relationship.target.value == "Paper"
        if spec.get("core_only") and not paper_endpoints:
            raise ValueError(f"projections.{name}.core_only requires paper endpoints")
        if "weight" in spec and (not isinstance(spec["weight"], str) or not spec["weight"].strip()):
            raise ValueError(f"projections.{name}.weight must be a nonempty property name")

    communities = config.get("communities")
    if not isinstance(communities, dict) or communities.get("fallback") != "louvain_networkx":
        raise ValueError("analysis config must select the implemented louvain_networkx fallback")
    seeds = communities.get("seeds")
    if not isinstance(seeds, list) or not seeds or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("communities.seeds must be a nonempty list of nonnegative integers")
    resolutions = communities.get("resolutions")
    if not isinstance(resolutions, list) or not resolutions or any(
        type(value) not in (int, float) or not math.isfinite(value) or value <= 0
        for value in resolutions
    ):
        raise ValueError("communities.resolutions must be a nonempty list of positive numbers")

    betweenness = config.get("betweenness")
    if (
        not isinstance(betweenness, dict)
        or betweenness.get("weighted_distance") != "inverse_positive_strength"
    ):
        raise ValueError("betweenness must use inverse_positive_strength distances")
    if type(betweenness.get("approximate")) is not bool:
        raise ValueError("betweenness.approximate must be boolean")
    _positive_int(betweenness.get("sample_nodes"), "betweenness.sample_nodes")

    robustness = config.get("robustness")
    if not isinstance(robustness, dict):
        raise ValueError("analysis config requires a robustness mapping")
    _positive_int(robustness.get("compare_top_k"), "robustness.compare_top_k")
    if not isinstance(robustness.get("stricter_evidence_filter_status"), str):
        raise ValueError("robustness.stricter_evidence_filter_status is required")
    return config, raw


def _validate_readiness(path: Path | None, graph: GraphArtifact, graph_raw: bytes) -> bytes:
    if path is None:
        raise ValueError("a matching post-build readiness receipt is required for non-synthetic analysis")
    raw = path.read_bytes()
    receipt = json.loads(raw)
    expected = {
        "status": "post_build_audit_ready",
        "graph_version": graph.graph_version,
        "graph_sha256": hashlib.sha256(graph_raw).hexdigest(),
        "preconstruction_gates_passed": True,
        "graph_construction": "completed",
    }
    if not isinstance(receipt, dict):
        raise ValueError("post-build readiness receipt must be a JSON object")
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError(f"readiness receipt {key} does not match the required post-build state")
    return raw


def _size_gates(graph: GraphArtifact, path: Path) -> tuple[dict, bytes, dict]:
    """Compute the quality-config size gates. Each is recorded as passed or failed, never raised."""
    raw = path.read_bytes()
    config = yaml.safe_load(raw)
    size = config.get("size") if isinstance(config, dict) else None
    if not isinstance(size, dict):
        raise ValueError("quality configuration requires a size mapping")
    required = (
        "min_domain_nodes",
        "min_resolved_core_researchers",
        "min_unique_factual_edges",
        "required_relation_types",
    )
    for key in required:
        _positive_int(size.get(key), f"quality.size.{key}")
    counts = graph_counts(graph)
    actual = {
        "min_domain_nodes": len(graph.nodes),
        "min_resolved_core_researchers": counts["resolved_core_researchers"],
        "min_unique_factual_edges": counts["unique_core_factual_edges"],
        "required_relation_types": len(counts["edges_by_relation"]),
    }
    passed = {
        "min_domain_nodes": actual["min_domain_nodes"] >= size["min_domain_nodes"],
        "min_resolved_core_researchers": actual["min_resolved_core_researchers"] >= size["min_resolved_core_researchers"],
        "min_unique_factual_edges": actual["min_unique_factual_edges"] >= size["min_unique_factual_edges"],
        "required_relation_types": (
            actual["required_relation_types"] == size["required_relation_types"]
            and actual["required_relation_types"] == len(Relation)
        ),
    }
    gates = {
        key: {"required": size[key], "actual": actual[key], "status": "passed" if passed[key] else "failed"}
        for key in required
    }
    summary = {"status": "passed" if all(passed.values()) else "failed", "gates": gates}
    return config, raw, summary


def _projection_graph(
    graph: GraphArtifact,
    spec: dict,
    name: str,
    edge_filter=None,
) -> nx.Graph:
    relation = Relation(spec["relation"])
    labels_value = spec.get("node_labels", spec.get("node_label"))
    labels = {labels_value} if isinstance(labels_value, str) else set(labels_value)
    core_only = spec.get("core_only", False)
    nodes = {node.id: node for node in graph.nodes}
    included_nodes = {
        node.id: node
        for node in graph.nodes
        if node.label.value in labels
        and (not core_only or node.label.value != "Paper" or node.properties.get("is_core") is True)
    }
    projected = nx.DiGraph() if spec["directed"] else nx.Graph()
    for node_id, node in sorted(included_nodes.items()):
        projected.add_node(node_id, label=node.label.value, name=node.name)
    weight_property = spec.get("weight")
    for edge in graph.edges:
        if (
            edge.relation != relation
            or edge.source_id not in included_nodes
            or edge.target_id not in included_nodes
        ):
            continue
        if edge_filter is not None and not edge_filter(edge):
            continue
        if core_only and any(
            nodes[identifier].properties.get("is_core") is not True
            for identifier in (edge.source_id, edge.target_id)
        ):
            continue
        strength = 1.0 if weight_property is None else edge.properties.get(weight_property)
        if type(strength) not in (int, float) or not math.isfinite(strength) or strength <= 0:
            raise ValueError(
                f"projection {name} edge {edge.edge_id} lacks positive finite weight {weight_property!r}"
            )
        projected.add_edge(
            edge.source_id,
            edge.target_id,
            strength=float(strength),
            distance=1.0 / float(strength),
            edge_id=edge.edge_id,
        )
    return projected


def _validated_strict_filter(value) -> dict:
    if not isinstance(value, dict) or not value:
        raise ValueError("strict_evidence_filter must be a nonempty frozen mapping")
    allowed_keys = {
        "minimum_evidence_records",
        "minimum_support_count",
        "allowed_evidence_kinds",
        "exclude_method_versions",
    }
    if set(value) - allowed_keys:
        raise ValueError("strict_evidence_filter contains unsupported criteria")
    if "minimum_evidence_records" in value:
        _positive_int(value["minimum_evidence_records"], "strict_evidence_filter.minimum_evidence_records")
    if "minimum_support_count" in value:
        _positive_int(value["minimum_support_count"], "strict_evidence_filter.minimum_support_count")
    if "allowed_evidence_kinds" in value:
        kinds = value["allowed_evidence_kinds"]
        allowed = {kind.value for kind in EvidenceKind}
        if (
            not isinstance(kinds, list)
            or not kinds
            or any(not isinstance(kind, str) or kind not in allowed for kind in kinds)
        ):
            raise ValueError(
                "strict_evidence_filter.allowed_evidence_kinds must be a nonempty list of evidence kinds"
            )
        if len(kinds) != len(set(kinds)):
            raise ValueError("strict_evidence_filter.allowed_evidence_kinds must not contain duplicates")
    if "exclude_method_versions" in value:
        versions = value["exclude_method_versions"]
        if not isinstance(versions, list) or any(not isinstance(item, str) or not item for item in versions):
            raise ValueError(
                "strict_evidence_filter.exclude_method_versions must be a list of nonempty strings"
            )
        if len(versions) != len(set(versions)):
            raise ValueError("strict_evidence_filter.exclude_method_versions must not contain duplicates")
    if not any((
        value.get("minimum_evidence_records", 1) > 1,
        "minimum_support_count" in value,
        "allowed_evidence_kinds" in value
        and set(value["allowed_evidence_kinds"]) != {kind.value for kind in EvidenceKind},
        bool(value.get("exclude_method_versions")),
    )):
        raise ValueError("strict_evidence_filter must define at least one stricter criterion")
    return value


def _strict_filter_hash(value: dict | None) -> str | None:
    """Hash the filter's canonical JSON representation for result provenance."""
    if value is None:
        return None
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _edge_passes_filter(edge, filter_spec: dict) -> bool:
    if len(edge.evidence_ids) < filter_spec.get("minimum_evidence_records", 1):
        return False
    allowed_kinds = filter_spec.get(
        "allowed_evidence_kinds", [kind.value for kind in EvidenceKind]
    )
    if edge.evidence_kind.value not in allowed_kinds:
        return False
    if edge.method_version in filter_spec.get("exclude_method_versions", []):
        return False
    if "minimum_support_count" in filter_spec:
        support_count = edge.properties.get("support_count", 0)
        if type(support_count) is not int or support_count < filter_spec["minimum_support_count"]:
            return False
    return True


def _round(value: float) -> float:
    return round(float(value), 12)


def _top(scores: dict[str, float], limit: int) -> list[dict]:
    return [
        {"node_id": node_id, "score": _round(score)}
        for node_id, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _rank_scores(scores: dict[str, float]) -> dict[str, float]:
    ordered = sorted(scores.items(), key=lambda item: (item[1], item[0]))
    ranks = {}
    index = 0
    while index < len(ordered):
        stop = index + 1
        while stop < len(ordered) and ordered[stop][1] == ordered[index][1]:
            stop += 1
        average_rank = ((index + 1) + stop) / 2
        for node_id, _ in ordered[index:stop]:
            ranks[node_id] = average_rank
        index = stop
    return ranks


def _spearman(first: dict[str, float], second: dict[str, float]) -> float | None:
    common = sorted(set(first) & set(second))
    if len(common) < 2:
        return None
    first_ranks = _rank_scores({node_id: first[node_id] for node_id in common})
    second_ranks = _rank_scores({node_id: second[node_id] for node_id in common})
    mean_first = statistics.mean(first_ranks.values())
    mean_second = statistics.mean(second_ranks.values())
    numerator = math.fsum(
        (first_ranks[node_id] - mean_first) * (second_ranks[node_id] - mean_second)
        for node_id in common
    )
    denominator = math.sqrt(
        math.fsum((first_ranks[node_id] - mean_first) ** 2 for node_id in common)
        * math.fsum((second_ranks[node_id] - mean_second) ** 2 for node_id in common)
    )
    return None if denominator == 0 else _round(numerator / denominator)


def _pagerank(
    graph: nx.DiGraph,
    *,
    alpha: float = 0.85,
    tolerance: float = 1e-12,
    max_iterations: int = 1000,
) -> dict[str, float]:
    """Power-iteration PageRank without an optional SciPy runtime dependency."""
    nodes = sorted(graph.nodes)
    if not nodes:
        return {}
    count = len(nodes)
    rank = {node: 1.0 / count for node in nodes}
    out_strength = {
        node: math.fsum(data["strength"] for _, _, data in graph.out_edges(node, data=True))
        for node in nodes
    }
    for _ in range(max_iterations):
        dangling_mass = math.fsum(rank[node] for node in nodes if out_strength[node] == 0)
        updated = {node: (1.0 - alpha + alpha * dangling_mass) / count for node in nodes}
        for source in nodes:
            denominator = out_strength[source]
            if denominator == 0:
                continue
            for _, target, data in graph.out_edges(source, data=True):
                updated[target] += alpha * rank[source] * data["strength"] / denominator
        error = math.fsum(abs(updated[node] - rank[node]) for node in nodes)
        rank = updated
        if error < tolerance:
            return rank
    raise ValueError(f"PageRank did not converge within {max_iterations} iterations")


def _component_sizes(graph: nx.Graph) -> list[int]:
    if graph.is_directed():
        components = nx.weakly_connected_components(graph)
    else:
        components = nx.connected_components(graph)
    return sorted((len(component) for component in components), reverse=True)


def _communities(graph: nx.Graph, seeds: list[int], resolutions: list[float]) -> list[dict]:
    if graph.is_directed():
        return []
    results = []
    for resolution in resolutions:
        for seed in seeds:
            if graph.number_of_nodes() == 0:
                groups = []
            elif graph.number_of_edges() == 0:
                groups = [{node} for node in graph.nodes]
            else:
                groups = nx.algorithms.community.louvain_communities(
                    graph,
                    weight="strength",
                    resolution=float(resolution),
                    seed=seed,
                )
            groups = sorted(
                (sorted(group) for group in groups),
                key=lambda group: (group[0] if group else "", group),
            )
            modularity = None
            if graph.number_of_edges() and groups:
                modularity = _round(
                    nx.algorithms.community.modularity(
                        graph,
                        [set(group) for group in groups],
                        weight="strength",
                        resolution=float(resolution),
                    )
                )
            results.append({
                "algorithm": "louvain_networkx",
                "seed": seed,
                "resolution": float(resolution),
                "community_count": len(groups),
                "community_sizes": sorted((len(group) for group in groups), reverse=True),
                "communities": groups,
                "modularity": modularity,
            })
    return results


def _summarize_projection(name: str, graph: nx.Graph, config: dict) -> dict:
    node_count, edge_count = graph.number_of_nodes(), graph.number_of_edges()
    degrees = dict(graph.degree())
    strengths = dict(graph.degree(weight="strength"))
    weights = [data["strength"] for _, _, data in graph.edges(data=True)]
    density = nx.density(graph) if node_count > 1 else 0.0
    betweenness = {}
    if node_count:
        settings = config["betweenness"]
        sample_size = settings["sample_nodes"]
        k = sample_size if settings["approximate"] and node_count > sample_size else None
        betweenness = nx.betweenness_centrality(
            graph,
            k=k,
            normalized=True,
            weight="distance",
            seed=config["random_seed"],
        )
    pagerank = {}
    if name == "core_citations" and node_count:
        pagerank = _pagerank(graph)

    communities_applicable = name in {"researcher_collaboration", "organization_collaboration"}
    communities = _communities(
        graph,
        config["communities"]["seeds"],
        [float(value) for value in config["communities"]["resolutions"]],
    ) if communities_applicable else []
    if graph.is_directed():
        strong_components = sorted(
            (len(component) for component in nx.strongly_connected_components(graph)),
            reverse=True,
        )
    else:
        strong_components = None
    limit = config["robustness"]["compare_top_k"]
    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "directed": graph.is_directed(),
        "density": _round(density),
        "isolate_count": sum(1 for value in degrees.values() if value == 0),
        "degree_mean": _round(statistics.mean(degrees.values())) if degrees else 0.0,
        "degree_max": max(degrees.values(), default=0),
        "strength_sum": _round(sum(strengths.values()) / 2),
        "edge_strength_min": _round(min(weights)) if weights else None,
        "edge_strength_mean": _round(statistics.mean(weights)) if weights else None,
        "edge_strength_max": _round(max(weights)) if weights else None,
        "weak_or_undirected_component_sizes": _component_sizes(graph),
        "strong_component_sizes": strong_components,
        "top_degree_strength": _top(strengths, limit),
        "top_betweenness": _top(betweenness, limit),
        "top_pagerank": _top(pagerank, limit),
        "communities_applicable": communities_applicable,
        "centrality_scores": {
            "degree_strength": {node_id: _round(score) for node_id, score in sorted(strengths.items())},
            "betweenness": {node_id: _round(score) for node_id, score in sorted(betweenness.items())},
            "pagerank": {node_id: _round(score) for node_id, score in sorted(pagerank.items())},
        },
        "communities": communities,
    }


def _sensitivity_comparison(base: dict, strict: dict, top_k: int) -> dict:
    comparisons = {}
    for metric, top_key in (
        ("degree_strength", "top_degree_strength"),
        ("betweenness", "top_betweenness"),
        ("pagerank", "top_pagerank"),
    ):
        first, second = base["centrality_scores"][metric], strict["centrality_scores"][metric]
        first_top = {item["node_id"] for item in base[top_key][:top_k]}
        second_top = {item["node_id"] for item in strict[top_key][:top_k]}
        denominator = min(len(first_top), len(second_top))
        overlap = len(first_top & second_top)
        comparisons[metric] = {
            "top_k": top_k,
            "overlap_count": overlap,
            "overlap_fraction_of_smaller_list": _round(overlap / denominator) if denominator else None,
            "spearman_on_common_nodes": _spearman(first, second),
            "common_node_count": len(set(first) & set(second)),
        }
    base_count, strict_count = base["node_count"], strict["node_count"]
    base_components = base["weak_or_undirected_component_sizes"]
    strict_components = strict["weak_or_undirected_component_sizes"]
    base_largest = base_components[0] if base_components else 0
    strict_largest = strict_components[0] if strict_components else 0
    base_share = base_largest / base_count if base_count else None
    strict_share = strict_largest / strict_count if strict_count else None
    return {
        "edge_retention_fraction": (
            _round(strict["edge_count"] / base["edge_count"])
            if base["edge_count"]
            else None
        ),
        "largest_component_share_base": _round(base_share) if base_share is not None else None,
        "largest_component_share_strict": _round(strict_share) if strict_share is not None else None,
        "largest_component_share_delta": (
            _round(strict_share - base_share)
            if strict_share is not None and base_share is not None
            else None
        ),
        "centralities": comparisons,
    }


def analyze_graph(
    input_path: Path,
    config_path: Path,
    output_path: Path,
    readiness_path: Path | None = None,
    quality_config_path: Path | None = None,
) -> dict:
    """Write deterministic projection metrics for a frozen graph artifact."""
    protected = {input_path.resolve(), config_path.resolve()}
    if readiness_path is not None:
        protected.add(readiness_path.resolve())
    if quality_config_path is not None:
        protected.add(quality_config_path.resolve())
    if output_path.resolve() in protected:
        raise ValueError("analysis output must differ from graph, configs, and readiness inputs")
    if output_path.exists() or output_path.is_symlink():
        raise ValueError("analysis output already exists; use a new versioned path")

    graph_raw = input_path.read_bytes()
    graph = GraphArtifact.model_validate_json(graph_raw)
    errors = validate_graph(graph)
    if errors:
        raise ValueError("graph fails structural validation: " + "; ".join(errors[:10]))
    config, config_raw = _load_config(config_path)
    readiness_raw = None
    quality_raw = None
    size_gates = None
    if not graph.is_synthetic:
        if config["status"] != "frozen":
            raise ValueError("real-graph analysis requires a frozen analysis configuration")
        robustness = config["robustness"]
        if robustness.get("stricter_evidence_filter_status") != "frozen" or not isinstance(
            robustness.get("strict_evidence_filter"), dict
        ):
            raise ValueError("real-graph analysis requires a frozen strict evidence-filter specification")
        if quality_config_path is None:
            raise ValueError("a quality config is required for non-synthetic analysis")
        # D040: a real graph needs neither a readiness receipt nor passing size gates.
        # The gates are computed and recorded as passed or failed in the output; a
        # historical receipt is still verified when one is supplied.
        _, quality_raw, size_gates = _size_gates(graph, quality_config_path)
        if readiness_path is not None:
            readiness_raw = _validate_readiness(readiness_path, graph, graph_raw)

    projections = {}
    for name, spec in config["projections"].items():
        projected = _projection_graph(graph, spec, name)
        projections[name] = _summarize_projection(name, projected, config)

    release_metrics = None if graph.is_synthetic else compute_release_metrics(graph, projections, config)

    strict_filter = config["robustness"].get("strict_evidence_filter")
    strict_filter_status = config["robustness"]["stricter_evidence_filter_status"]
    run_sensitivity = strict_filter_status == "frozen" and isinstance(strict_filter, dict)
    if not graph.is_synthetic and not run_sensitivity:
        raise ValueError("real-graph analysis requires a frozen strict evidence-filter specification")
    strict_projection_metrics = {}
    sensitivity = {}
    if run_sensitivity:
        strict_filter = _validated_strict_filter(strict_filter)
        for name, spec in config["projections"].items():
            strict_graph = _projection_graph(
                graph, spec, name, edge_filter=lambda edge: _edge_passes_filter(edge, strict_filter)
            )
            strict_projection_metrics[name] = _summarize_projection(name, strict_graph, config)
            sensitivity[name] = _sensitivity_comparison(
                projections[name], strict_projection_metrics[name], config["robustness"]["compare_top_k"]
            )
    result = {
        "status": "synthetic_protocol_only" if graph.is_synthetic else "analysis_metrics_only",
        "analysis_method_version": METHOD_VERSION,
        "graph_version": graph.graph_version,
        "is_synthetic": graph.is_synthetic,
        "release_status": "ineligible_synthetic" if graph.is_synthetic else "not_certified",
        "analysis_config_status": config["status"],
        "input_sha256": hashlib.sha256(graph_raw).hexdigest(),
        "analysis_config_sha256": hashlib.sha256(config_raw).hexdigest(),
        "quality_config_sha256": hashlib.sha256(quality_raw).hexdigest() if quality_raw is not None else None,
        "readiness_sha256": hashlib.sha256(readiness_raw).hexdigest() if readiness_raw is not None else None,
        "size_gates": size_gates,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "graph_counts": graph_counts(graph),
        "projections": projections,
        "release_metrics": release_metrics,
        "strict_projections": strict_projection_metrics,
        "robustness": {
            "strict_evidence_filter_status": strict_filter_status,
            "strict_evidence_filter_sha256": _strict_filter_hash(strict_filter),
            "sensitivity_comparison": "computed" if run_sensitivity else "not_computed",
            "per_projection": sensitivity,
        },
        "business_findings": {
            "status": "not_generated" if graph.is_synthetic else "candidate_metrics_only",
            "reason": "source-backed findings prose is maintained separately; candidate tables do not establish semantic accuracy",
        },
        "limitations": [
            "Structural validation does not establish semantic correctness or coverage.",
            "Community assignments use the configured NetworkX Louvain fallback; GDS was not used.",
            "Topic labels are inferred and await independent human review; topic findings are provisional.",
            "Strict-evidence sensitivity results describe robustness to the configured filter and are not accuracy evidence.",
            "Citation counts use current in-scope metadata and are not normalized for paper age or exposure time.",
            "Country mixing retains an unknown category where organization country metadata is absent.",
            "Synthetic output is a protocol check and cannot support a research or release claim.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return result
