"""Offline unit tests for the Research Explorer backend using mocked Neo4j repository."""

from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

APP_DIR = Path(__file__).resolve().parents[2]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from backend.config import EXPECTED_GRAPH_VERSION, load_settings  # noqa: E402
from backend.main import create_app  # noqa: E402
from backend.repositories.artifact_store import ArtifactStore  # noqa: E402
from backend.repositories.neo4j_repo import fold_diacritics, validate_labels, validate_relations  # noqa: E402


class FakeNeo4jRepository:
    """In-memory mock repository for fast offline unit testing."""

    def __init__(self) -> None:
        self.nodes = {
            "researcher:openalex:A5017743551": {
                "id": "researcher:openalex:A5017743551",
                "name": "Bo An",
                "_label": "Researcher",
                "resolution_status": "resolved",
                "identity_method": "openalex_author_id",
                "openalex_id": "A5017743551",
            },
            "researcher:openalex:A5000000572": {
                "id": "researcher:openalex:A5000000572",
                "name": "Piotr Faliszewski",
                "_label": "Researcher",
                "resolution_status": "resolved",
                "identity_method": "openalex_author_id",
                "openalex_id": "A5000000572",
                "orcid": "0000-0002-0332-4364",
            },
            "researcher:openalex:A5024584819": {
                "id": "researcher:openalex:A5024584819",
                "name": "Tüomas Sandholm",
                "_label": "Researcher",
                "resolution_status": "resolved",
                "identity_method": "openalex_author_id",
                "openalex_id": "A5024584819",
            },
            "paper:aaai:2021:17325": {
                "id": "paper:aaai:2021:17325",
                "name": "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting",
                "_label": "Paper",
                "year": 2021,
                "is_core": True,
                "track": "main",
                "official_url": "https://ojs.aaai.org/index.php/AAAI/article/view/17325",
                "doi": "10.1609/aaai.v35i12.17325",
            },
            "organization:I183067930": {
                "id": "organization:I183067930",
                "name": "Shanghai Jiao Tong University",
                "_label": "Organization",
                "sector": "academia",
                "country_code": "CN",
                "openalex_id": "I183067930",
            },
            "topic:representation-learning": {
                "id": "topic:representation-learning",
                "name": "Representation learning",
                "_label": "Topic",
                "level": "leaf",
                "parent_id": "topic:learning-methods",
                "definition": "Learning representations of data.",
            },
            "venue:aaai": {
                "id": "venue:aaai",
                "name": "AAAI Conference on Artificial Intelligence",
                "_label": "Venue",
            },
        }
        self.sample_edge = {
            "edge_id": "edge:sample123",
            "relation": "COAUTHORED_WITH",
            "source": "researcher:openalex:A5000000572",
            "target": "researcher:openalex:A5017743551",
            "source_name": "Piotr Faliszewski",
            "target_name": "Bo An",
            "source_label": "Researcher",
            "target_label": "Researcher",
            "directed": False,
            "symmetric": True,
            "evidence_kind": "derived",
            "evidence_ids": ["evidence:derived:sample123"],
            "support_count": 3,
            "fractional_weight": 0.75,
            "method_version": "core-derivation-v1",
            "graph_version": EXPECTED_GRAPH_VERSION,
            "validation_status": "accepted",
            "properties": {"support_count": 3, "fractional_weight": 0.75},
        }

    def verify_inventory(self, *, use_cache: bool = True) -> dict:
        return {
            "connected": True,
            "endpoint": "bolt://127.0.0.1:7689",
            "expected_graph_version": EXPECTED_GRAPH_VERSION,
            "observed_graph_versions": [EXPECTED_GRAPH_VERSION],
            "database_verified": True,
            "nodes_by_label": {
                "Researcher": 32189,
                "Paper": 13617,
                "Organization": 2047,
                "Topic": 20,
                "Venue": 2,
            },
            "edges_by_relation": {
                "AUTHORED": 50437,
                "AFFILIATED_WITH": 38664,
                "PUBLISHED_IN": 13617,
                "CITES": 7308,
                "HAS_TOPIC": 14222,
                "SUBTOPIC_OF": 16,
                "COAUTHORED_WITH": 80482,
                "COLLABORATED_WITH": 13031,
                "RESEARCHES_TOPIC": 5622,
                "CONTRIBUTES_TO_TOPIC": 2332,
            },
            "total_nodes": 47875,
            "total_edges": 225731,
            "warnings": [],
        }

    def get_node_by_id(self, node_id: str) -> dict | None:
        return self.nodes.get(node_id)

    def get_nodes_by_ids(self, node_ids: list[str]) -> dict[str, dict]:
        return {nid: self.nodes[nid] for nid in node_ids if nid in self.nodes}

    def get_paper_venues(self, paper_ids: list[str]) -> dict[str, str]:
        return {pid: "venue:aaai" for pid in paper_ids}

    def get_induced_edges(self, node_ids: list[str], **_kwargs) -> list[dict]:
        if set(node_ids) >= {"researcher:openalex:A5000000572", "researcher:openalex:A5017743551"}:
            return [self.sample_edge]
        return []

    def search_nodes(self, query: str, *, labels=None, limit=30, **_kwargs):
        q = query.strip().lower()
        q_folded = fold_diacritics(query)
        matches = []
        for n in self.nodes.values():
            if labels and n["_label"] not in labels:
                continue
            name_low = n["name"].lower()
            name_folded = fold_diacritics(n["name"])
            if not q or q in name_low or q_folded in name_folded or q in n["id"].lower():
                item = dict(n)
                item["_match_rank"] = 0 if (q == name_low or q_folded == name_folded) else 1
                matches.append(item)
        counts = {}
        for m in matches:
            counts[m["_label"]] = counts.get(m["_label"], 0) + 1
        return counts, matches[:limit]

    def get_node_relation_counts(self, node_id: str) -> dict[str, int]:
        return {"COAUTHORED_WITH": 12, "AUTHORED": 18} if node_id in self.nodes else {}

    def get_node_connected_groups(self, _node_id: str, **_kwargs) -> list[dict]:
        return [
            {
                "relation": "COAUTHORED_WITH",
                "direction": "undirected",
                "evidence_kind": "derived",
                "total_count": 1,
                "items": [
                    {
                        "edge_id": "edge:sample123",
                        "neighbor_id": "researcher:openalex:A5000000572",
                        "neighbor_name": "Piotr Faliszewski",
                        "neighbor_label": "Researcher",
                        "support_count": 3,
                        "fractional_weight": 0.75,
                    }
                ],
            }
        ]

    def get_neighborhood(self, node_id: str, **_kwargs):
        other = self.nodes["researcher:openalex:A5000000572"]
        return 1, [other], [self.sample_edge]

    def get_edge_by_id(self, edge_id: str) -> dict | None:
        if edge_id != "edge:sample123":
            return None
        return {
            "edge": self.sample_edge,
            "source_node": self.nodes["researcher:openalex:A5000000572"],
            "target_node": self.nodes["researcher:openalex:A5017743551"],
        }

    def get_edges_by_ids(self, _edge_ids: list[str]) -> list[dict]:
        return []

    def resolve_derived_supporting_papers_cypher(self, *_args, **_kwargs) -> list[dict]:
        return [
            {
                "paper_id": "paper:aaai:2021:17325",
                "title": "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting",
                "year": 2021,
                "venue": "AAAI Conference on Artificial Intelligence",
                "doi": "10.1609/aaai.v35i12.17325",
                "official_url": "https://ojs.aaai.org/index.php/AAAI/article/view/17325",
            }
        ]

    def find_shortest_path(self, source_id: str, target_id: str, **_kwargs):
        if source_id in self.nodes and target_id in self.nodes:
            return [self.nodes[source_id], self.nodes[target_id]], [self.sample_edge]
        return [], []

    def compare_entities(self, _left_id: str, _right_id: str) -> dict:
        return {
            "direct_edges": [self.sample_edge],
            "shared_neighbors": [self.nodes["organization:I183067930"]],
            "shared_papers": self.resolve_derived_supporting_papers_cypher(),
        }

    def get_organization_collaboration_subgraph(self, **_kwargs):
        return [self.nodes["organization:I183067930"]], []

    def get_citation_subgraph(self, **_kwargs):
        return [self.nodes["paper:aaai:2021:17325"]], []

    def get_heterogeneous_subgraph(self, **_kwargs):
        return list(self.nodes.values()), [self.sample_edge]

    def query_table_nodes(self, **_kwargs):
        return len(self.nodes), list(self.nodes.values())

    def query_table_edges(self, **_kwargs):
        return 1, [self.sample_edge]

    def close(self) -> None:
        pass


@pytest.fixture(scope="module")
def unit_client() -> TestClient:
    cfg = load_settings()
    fake_store = ArtifactStore(
        summary_path=cfg.summary_artifact_path,
        analysis_path=cfg.analysis_artifact_path,
        network_views_path=cfg.network_views_path,
        audit_results_path=cfg.audit_results_path,
        graph_artifact_path=Path("/nonexistent/graph.json"),
    )
    fake_repo = FakeNeo4jRepository()
    app = create_app(cfg, repo=fake_repo, store=fake_store, background_warmup=False)
    return TestClient(app)


def test_allowlist_validation():
    assert validate_labels(["Researcher", "Paper"]) == ["Researcher", "Paper"]
    with pytest.raises(ValueError, match="Unsupported node label"):
        validate_labels(["MaliciousLabel"])
    assert validate_relations(["CITES", "AUTHORED"]) == ["CITES", "AUTHORED"]
    with pytest.raises(ValueError, match="Unsupported relationship predicate"):
        validate_relations(["DROP_DATABASE"])


def test_health_and_security_headers(unit_client: TestClient):
    res = unit_client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["expected_graph_version"] == EXPECTED_GRAPH_VERSION
    assert data["database_verified"] is True
    assert data["total_nodes"] == 47875
    assert data["total_edges"] == 225731
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in res.headers["Content-Security-Policy"]


def test_disallowed_http_methods_rejected(unit_client: TestClient):
    for method in ("DELETE", "PUT", "PATCH"):
        res = unit_client.request(method, "/api/health")
        assert res.status_code == 405


def test_summary_and_schema_endpoints(unit_client: TestClient):
    sum_res = unit_client.get("/api/graph/summary")
    assert sum_res.status_code == 200
    sdata = sum_res.json()
    assert sdata["graph_version"] == EXPECTED_GRAPH_VERSION
    assert sdata["unique_core_factual_edges"] == 110026
    q = sdata["quality"]
    assert q["human_validation_performed"] is False
    assert q["affiliation_positions_resolved"] == 48259
    assert q["affiliation_positions_eligible"] == 65469
    assert q["affiliation_target"] == pytest.approx(0.80)
    assert q["affiliation_status"] == "failed"
    assert q["topic_papers_labeled"] == 11575
    assert q["topic_papers_eligible"] == 13617
    assert q["topic_coverage_target"] == pytest.approx(0.80)
    assert q["topic_coverage_status"] == "passed"
    assert q["topic_precision"] == pytest.approx(0.68627451)
    assert q["topic_precision_target"] == pytest.approx(0.95)
    assert q["topic_precision_status"] == "failed"
    assert q["topic_micro_f1"] == pytest.approx(0.46666667)

    an_res = unit_client.get("/api/analytics/overview")
    assert an_res.status_code == 200
    an_data = an_res.json()
    assert an_data["quality"]["affiliation_positions_resolved"] == 48259
    assert an_data["quality"]["affiliation_positions_eligible"] == 65469

    sch_res = unit_client.get("/api/graph/schema")
    assert sch_res.status_code == 200
    scdata = sch_res.json()
    assert len(scdata["labels"]) == 5
    assert len(scdata["predicates"]) == 10


def test_search_and_input_validation(unit_client: TestClient):
    res = unit_client.get("/api/search", params={"q": "Bo An"})
    assert res.status_code == 200
    body = res.json()
    assert body["total_matches"] >= 1
    assert body["results"][0]["id"] == "researcher:openalex:A5017743551"
    assert body["results"][0]["full_metrics"]["betweenness"] > 0

    # Accent-insensitive retrieval: unaccented query matches stored diacritic spelling
    acc = unit_client.get("/api/search", params={"q": "Tuomas Sandholm"})
    assert acc.status_code == 200
    acc_body = acc.json()
    assert acc_body["total_matches"] >= 1
    assert acc_body["results"][0]["name"] == "Tüomas Sandholm"

    # Invalid year range rejected by FastAPI validation
    bad = unit_client.get("/api/search", params={"year_min": 1990})
    assert bad.status_code == 422


def test_node_detail_and_neighbors(unit_client: TestClient):
    res = unit_client.get("/api/nodes/researcher:openalex:A5017743551")
    assert res.status_code == 200
    detail = res.json()
    assert detail["node"]["name"] == "Bo An"
    assert detail["total_degree"] == 30

    missing = unit_client.get("/api/nodes/researcher:openalex:NONEXISTENT")
    assert missing.status_code == 404

    nb_res = unit_client.get("/api/nodes/researcher:openalex:A5017743551/neighbors", params={"limit": 10})
    assert nb_res.status_code == 200
    nb = nb_res.json()
    assert nb["center_id"] == "researcher:openalex:A5017743551"
    assert len(nb["nodes"]) == 2
    assert len(nb["edges"]) == 1


def test_edge_evidence_fallback(unit_client: TestClient):
    res = unit_client.get("/api/edges/edge:sample123/evidence")
    assert res.status_code == 200
    ev = res.json()
    assert ev["edge"]["relation"] == "COAUTHORED_WITH"
    assert ev["ledger_source"] == "neo4j_fallback"
    assert len(ev["supporting_papers"]) == 1
    assert "1/(k-1)" in ev["derivation_explanation"]


def test_paths_and_compare_and_tables(unit_client: TestClient):
    path_res = unit_client.post(
        "/api/paths",
        json={
            "source_id": "researcher:openalex:A5000000572",
            "target_id": "researcher:openalex:A5017743551",
            "mode": "collaboration",
            "max_hops": 2,
        },
    )
    assert path_res.status_code == 200
    assert path_res.json()["found"] is True

    cmp_res = unit_client.get(
        "/api/compare",
        params={
            "left_id": "researcher:openalex:A5000000572",
            "right_id": "researcher:openalex:A5017743551",
        },
    )
    assert cmp_res.status_code == 200
    assert len(cmp_res.json()["shared_papers"]) == 1

    tbl_n = unit_client.get("/api/table/nodes", params={"page": 1, "page_size": 10})
    assert tbl_n.status_code == 200
    assert tbl_n.json()["total"] >= 1

    tbl_e = unit_client.get("/api/table/edges", params={"page": 1, "page_size": 10})
    assert tbl_e.status_code == 200
    assert tbl_e.json()["total"] == 1
