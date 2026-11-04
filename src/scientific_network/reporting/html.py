"""A standalone, read-only graph report; never collects data or queries Neo4j."""

import base64
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import networkx as nx

from scientific_network.collect.storage import digest, read_config, write_bytes
from scientific_network.contracts import GraphArtifact
from scientific_network.graph.schema import RELATIONSHIPS
from scientific_network.graph.validate import graph_counts, validate_graph

VERSION = "standalone-html-report-v1"
ASSETS = Path(__file__).parent / "assets"
SAFE_PROPERTIES = {"year", "official_url", "track", "is_core", "official_author_count",
    "resolution_status", "orcid", "openalex_ids", "name_variants", "sector", "ror",
    "country_code", "normalization_policy", "level", "taxonomy_version", "definition",
    "taxonomy_status", "identity_method", "independent_audit"}


def report_payload(graph_path: Path, metrics_path: Path, quality_path: Path, scope_path: Path) -> dict:
    graph_bytes = graph_path.read_bytes()
    graph = GraphArtifact.model_validate_json(graph_bytes)
    metrics = json.loads(metrics_path.read_text())
    quality, scope = read_config(quality_path), read_config(scope_path)
    errors = validate_graph(graph, require_derived=True,
        max_topic_labels=quality["topics"]["max_labels_per_paper"],
        researcher_min=quality["derived"]["researcher_topic_min_distinct_papers"],
        organization_min=quality["derived"]["organization_topic_min_distinct_papers"])
    if errors:
        raise ValueError("report blocked by structural graph errors: " + "; ".join(errors[:3]))
    versions = metrics.get("versions", {})
    for key, path in (("graph", graph_path), ("quality_config", quality_path), ("corpus_config", scope_path)):
        if versions.get(key, {}).get("sha256") != digest(path.read_bytes()):
            raise ValueError(f"{key} does not match the recorded metrics; choose matching artifacts")
    counts = graph_counts(graph)
    if metrics.get("graph_version") != graph.graph_version or metrics.get("counts") != counts:
        raise ValueError("graph version/counts differ from the recorded metrics")
    by_id = {n.id: n for n in graph.nodes}
    evidence = {e.id: json.loads(e.model_dump_json()) for e in graph.evidence}
    venues = {e["venue_id"]: e["name"] for e in scope["editions"]}
    paper_venue = {e.source_id: e.target_id for e in graph.edges if e.relation == "PUBLISHED_IN"}
    if any(v not in venues for v in paper_venue.values()):
        raise ValueError("graph venue missing from the supplied scope configuration")
    affiliations = defaultdict(set)
    for triple in graph.affiliation_observations:
        affiliations[triple.researcher_id, triple.organization_id].add(triple.paper_id)
    edges = []
    for edge in graph.edges:
        papers = set()
        if edge.relation in {"AUTHORED", "PUBLISHED_IN", "HAS_TOPIC", "CITES"}:
            papers = {n for n in (edge.source_id, edge.target_id) if by_id[n].label == "Paper"}
        elif edge.relation == "AFFILIATED_WITH":
            papers = affiliations[edge.source_id, edge.target_id]
        elif edge.evidence_kind == "derived":
            papers = {p for eid in edge.evidence_ids for p in evidence[eid]["support_paper_ids"]}
        edges.append({**json.loads(edge.model_dump_json()), "support_papers": sorted(papers)})
    nodes = [{"id": n.id, "label": n.label, "name": n.name,
              "properties": {k: v for k, v in n.properties.items() if k in SAFE_PROPERTIES}}
             for n in sorted(graph.nodes, key=lambda n: n.id)]
    # Layouts describe the current snapshot only. Their distances are not SNA scores.
    presets = {
        "all": ({n["id"] for n in nodes}, {str(r) for r in RELATIONSHIPS}),
        "factual": ({n["id"] for n in nodes if n["label"] != "Topic"},
                    {"AUTHORED", "AFFILIATED_WITH", "PUBLISHED_IN", "CITES"}),
        "coauthors": ({n["id"] for n in nodes if n["label"] == "Researcher"}, {"COAUTHORED_WITH"}),
        "organizations": ({n["id"] for n in nodes if n["label"] == "Organization"}, {"COLLABORATED_WITH"}),
    }
    layouts = {}
    for preset, (ids, relations) in presets.items():
        drawing = nx.Graph()
        drawing.add_nodes_from(sorted(ids))
        drawing.add_edges_from((e["source_id"], e["target_id"]) for e in edges if e["relation"] in relations)
        positions = nx.spring_layout(drawing, seed=42, iterations=160, weight=None,
                                     k=max(0.15, len(drawing) ** -0.5) if drawing else 0.15)
        layouts[preset] = {identifier: [round(float(x) * 490 + 550, 3), round(float(y) * 280 + 325, 3)]
                           for identifier, (x, y) in positions.items()}
    coverage = []
    for row in metrics["by_venue"]:
        available = row["status"] in {"collected", "legacy_preserved"}
        coverage.append({**row, "name": venues[row["venue_id"]],
            "included_roster": row["included_roster"] if available else None,
            "excluded_roster": row["excluded_roster"] if available else None})
    topic_counts = Counter(e.target_id for e in graph.edges if e.relation == "HAS_TOPIC")
    topics = sorted([{"id": n.id, "name": n.name, "papers": topic_counts[n.id]}
        for n in graph.nodes if n.label == "Topic" and n.properties.get("level") == "leaf"],
        key=lambda row: (-row["papers"], row["name"]))
    return {"report_version": VERSION, "graph_version": graph.graph_version,
        "generated_at": datetime.now(ZoneInfo("Asia/Bangkok")).isoformat(),
        "snapshot_at": metrics["recorded_at"], "is_synthetic": graph.is_synthetic,
        "nodes": nodes, "edges": edges, "evidence": evidence, "layouts": layouts,
        "paper_venue": paper_venue, "venue_names": venues, "counts": counts,
        "scope": metrics["scope"], "splits": metrics["splits"], "collection": metrics["collection"],
        "extraction": {k: metrics["extraction"][k] for k in ("by_status", "papers_with_header_affiliations")},
        "coverage": metrics["coverage"], "by_venue": coverage, "topics": topics,
        "unresolved_sources": metrics["unresolved_sources"], "size_targets": quality["size"],
        "verification_recorded": metrics["verification"], "structural_validation": "passed",
        "methods": metrics["methods"], "classifier_method": metrics["classifier_method"],
        "inputs": {key: {"name": path.name, "sha256": digest(path.read_bytes())}
            for key, path in (("graph", graph_path), ("metrics", metrics_path),
                              ("quality", quality_path), ("scope", scope_path))}}


def render_report(graph_path: Path, metrics_path: Path, quality_path: Path,
                  scope_path: Path, output: Path) -> dict:
    if output.exists() or output.is_symlink() or output.resolve() in {
        p.resolve() for p in (graph_path, metrics_path, quality_path, scope_path)
    }:
        raise ValueError("choose a new HTML output path distinct from the inputs")
    payload = report_payload(graph_path, metrics_path, quality_path, scope_path)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Source names and excerpts are untrusted text, including inside script elements.
    data = data.replace("<", "\\u003c").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    fonts = "\n".join(
        "@font-face{font-family:Geist;font-style:normal;font-weight:" + weight +
        ";font-display:swap;src:url(data:font/ttf;base64," +
        base64.b64encode((ASSETS / name).read_bytes()).decode() + ") format('truetype')}"
        for name, weight in (("Geist-regular.ttf", "400"), ("Geist-semibold.ttf", "600")))
    page = (ASSETS / "report.html").read_text()
    page = page.replace("<!-- REPORT_STYLE -->", "<style>" + fonts + "\n" + (ASSETS / "report.css").read_text() + "</style>")
    page = page.replace("<!-- REPORT_DATA -->", '<script id="report-data" type="application/json">' + data + "</script>")
    page = page.replace("<!-- REPORT_SCRIPT -->", "<script>" + (ASSETS / "report.js").read_text() + "</script>")
    # Include the bundled font's license within the standalone artifact.
    license_text = (ASSETS / "OFL.txt").read_text().replace("--", "—")
    page += "\n<!-- Embedded Geist font license:\n" + license_text + "\n-->\n"
    write_bytes(output, page.encode())
    return {"stage": "report", "status": "written", "output": str(output),
        "report_version": VERSION, "graph_version": payload["graph_version"],
        "nodes": len(payload["nodes"]), "edges": len(payload["edges"]),
        "output_sha256": digest(output.read_bytes()), "bytes": output.stat().st_size,
        "standalone": True, "semantic_accuracy": "not_measured_by_this_report"}
