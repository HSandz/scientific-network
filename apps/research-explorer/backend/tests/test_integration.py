"""Read-only integration tests against the live `neo4j-five-year` database on port 7689."""

from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

APP_DIR = Path(__file__).resolve().parents[2]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from backend.config import (  # noqa: E402
    EXPECTED_EDGES_BY_RELATION,
    EXPECTED_GRAPH_VERSION,
    EXPECTED_NODES_BY_LABEL,
    EXPECTED_TOTAL_EDGES,
    EXPECTED_TOTAL_NODES,
    load_settings,
)
from backend.main import create_app  # noqa: E402
from backend.repositories.neo4j_repo import Neo4jRepository  # noqa: E402


@pytest.fixture(scope="module")
def live_client():
    cfg = load_settings()
    repo = Neo4jRepository(cfg)
    inv = repo.verify_inventory(use_cache=False)
    if not inv["connected"]:
        repo.close()
        pytest.skip(f"Live neo4j-five-year database is not reachable at {cfg.neo4j_uri}: {inv['warnings']}")
    app = create_app(cfg, repo=repo, background_warmup=False)
    with TestClient(app) as client:
        yield client
    repo.close()


def test_live_health_and_exact_release_inventory(live_client: TestClient):
    res = live_client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["neo4j_connected"] is True
    assert data["database_verified"] is True
    assert data["expected_graph_version"] == EXPECTED_GRAPH_VERSION
    assert data["observed_graph_versions"] == [EXPECTED_GRAPH_VERSION]
    assert data["total_nodes"] == EXPECTED_TOTAL_NODES
    assert data["total_edges"] == EXPECTED_TOTAL_EDGES
    assert data["warnings"] == []

    sum_res = live_client.get("/api/graph/summary")
    assert sum_res.status_code == 200
    sdata = sum_res.json()
    assert sdata["nodes_by_label"] == EXPECTED_NODES_BY_LABEL
    assert sdata["edges_by_relation"] == EXPECTED_EDGES_BY_RELATION


def test_live_global_search_beyond_top_100_illustration(live_client: TestClient):
    # Piotr Faliszewski is not in the top-8 labeled illustration but is in the full 32,189-researcher DB
    res = live_client.get("/api/search", params={"q": "Piotr Faliszewski", "label": ["Researcher"]})
    assert res.status_code == 200
    data = res.json()
    assert data["total_matches"] >= 1
    assert any(item["id"] == "researcher:openalex:A5000000572" for item in data["results"])

    # Search for a specific paper by title substring
    p_res = live_client.get("/api/search", params={"q": "Undergraduate Games Corpus", "label": ["Paper"]})
    assert p_res.status_code == 200
    pdata = p_res.json()
    assert any(item["id"] == "paper:aaai:2021:16071" for item in pdata["results"])

    # Accent-insensitive search retrieves stored diacritic name without merging or modifying Neo4j
    t_res = live_client.get("/api/search", params={"q": "Tuomas Sandholm", "label": ["Researcher"]})
    assert t_res.status_code == 200
    tdata = t_res.json()
    assert tdata["total_matches"] >= 1
    assert any("Sandholm" in item["name"] and item["name"] == "Tüomas Sandholm" for item in tdata["results"])


def test_live_all_four_exploration_modes(live_client: TestClient):
    for mode in ("researchers", "organizations", "citations", "heterogeneous"):
        res = live_client.get(f"/api/views/{mode}", params={"limit": 40})
        assert res.status_code == 200
        body = res.json()
        assert body["view"] == mode
        assert body["displayed_node_count"] > 0
        assert body["displayed_edge_count"] > 0
        assert body["full_node_count"] >= body["displayed_node_count"]


def test_live_community_and_sector_filtering(live_client: TestClient):
    # Filter Mode A by a known Louvain community
    res = live_client.get("/api/views/researchers", params={"community_id": "community:00058", "limit": 50})
    assert res.status_code == 200
    body = res.json()
    assert body["displayed_node_count"] > 0
    assert all(n["full_metrics"]["community_id"] == "community:00058" for n in body["nodes"])

    # Filter Mode B by cross_sector_only
    org_res = live_client.get("/api/views/organizations", params={"cross_sector_only": True, "limit": 40})
    assert org_res.status_code == 200
    org_body = org_res.json()
    node_sectors = {n["id"]: n["sector"] for n in org_body["nodes"]}
    for edge in org_body["edges"]:
        if edge["relation"] == "COLLABORATED_WITH":
            assert node_sectors[edge["source"]] != node_sectors[edge["target"]]


def test_live_directional_citation_neighborhood_and_evidence(live_client: TestClient):
    # Paper `paper:aaai:2021:17325` (Informer) has 51 incoming citations in-scope
    incoming = live_client.get(
        "/api/nodes/paper:aaai:2021:17325/neighbors",
        params={"relations": ["CITES"], "direction": "incoming", "limit": 60},
    )
    assert incoming.status_code == 200
    inc_data = incoming.json()
    assert inc_data["total_incident_edges"] == 51
    cites_to_center = [e for e in inc_data["edges"] if e["target"] == "paper:aaai:2021:17325"]
    assert len(cites_to_center) == 51

    # Inspect evidence of the first citation edge
    sample_edge_id = cites_to_center[0]["edge_id"]
    ev_res = live_client.get(f"/api/edges/{sample_edge_id}/evidence")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["edge"]["edge_id"] == sample_edge_id
    assert ev_data["edge"]["relation"] == "CITES"
    assert len(ev_data["evidence_records"]) >= 1
    assert len(ev_data["supporting_papers"]) >= 1


def test_live_analytics_overview_and_path_discovery(live_client: TestClient):
    an_res = live_client.get("/api/analytics/overview")
    assert an_res.status_code == 200
    an = an_res.json()
    assert an["graph_version"] == EXPECTED_GRAPH_VERSION
    assert len(an["annual_counts"]["rows"]) == 5
    assert an["bridge_researchers"]["top_researchers"][0]["researcher"] == "Bo An"

    # Find path between two collaborating organizations
    p_res = live_client.post(
        "/api/paths",
        json={
            "source_id": "organization:I183067930",
            "target_id": "organization:I2250653659",
            "mode": "collaboration",
            "max_hops": 2,
        },
    )
    assert p_res.status_code == 200
    pdata = p_res.json()
    assert pdata["found"] is True
    assert pdata["hop_count"] == 1

    # Verify paginated table endpoints return non-empty items
    tn_res = live_client.get("/api/table/nodes", params={"label": "Researcher", "page": 1, "page_size": 10})
    assert tn_res.status_code == 200
    assert len(tn_res.json()["items"]) == 10

    te_res = live_client.get("/api/table/edges", params={"relation": "COAUTHORED_WITH", "page": 1, "page_size": 10})
    assert te_res.status_code == 200
    assert len(te_res.json()["items"]) == 10


def test_support_thresholds_do_not_filter_factual_citations(live_client):
    """Thresholds are meaningful for aggregate R7/R8, never binary citation facts."""
    endpoint = '/api/nodes/paper:aaai:2021:17325/neighbors'
    params = {'relations': 'CITES', 'direction': 'incoming', 'limit': 20}
    base = live_client.get(endpoint, params=params)
    filtered = live_client.get(endpoint, params={**params, 'min_support': 10, 'min_weight': 20})
    assert base.status_code == filtered.status_code == 200
    assert base.json()['edges']
    assert {e['edge_id'] for e in base.json()['edges']} == {e['edge_id'] for e in filtered.json()['edges']}


def test_curated_overview_never_silently_ignores_paper_filters(live_client):
    response = live_client.get('/api/views/heterogeneous', params={'year_min': 2023, 'venue': 'venue:ijcai'})
    assert response.status_code == 422
    assert 'Researcher → Paper → Topic' in response.json()['detail']
    response = live_client.get('/api/views/heterogeneous', params={'preset': 'researcher_paper_topic', 'year_min': 2023, 'year_max': 2023, 'venue': 'venue:ijcai', 'topic_id': 'topic:causal-inference'})
    assert response.status_code == 200
    papers = [n for n in response.json()['nodes'] if n['label'] == 'Paper']
    assert papers
    assert all(n['year'] == 2023 and n['venue'] == 'venue:ijcai' for n in papers)


def test_live_collaboration_paper_windows_and_frozen_edge_weights(live_client):
    for mode in ('researchers', 'organizations'):
        supports = []
        for year, venue in ((2021, 'aaai'), (2025, 'ijcai')):
            response = live_client.get(f'/api/views/{mode}', params={'limit': 60, 'year_min': year, 'year_max': year, 'venue': f'venue:{venue}'})
            assert response.status_code == 200, response.text
            edges = response.json()['edges']
            assert edges
            paper_ids = set()
            for edge in edges:
                support = edge['properties']['in_window_support_paper_ids']
                assert support and all(i.startswith(f'paper:{venue}:{year}:') for i in support)
                assert len(set(support)) == edge['properties']['in_window_support_count']
                assert edge['support_count'] >= len(support)
                paper_ids.update(support)
            original = live_client.get(f"/api/edges/{edges[0]['edge_id']}").json()
            assert original['fractional_weight'] == edges[0]['fractional_weight']
            assert original['support_count'] == edges[0]['support_count']
            supports.append(paper_ids)
        assert not supports[0] & supports[1]
