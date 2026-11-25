"""Offline & mocked tests for Phase 5 Research Trend Navigator API endpoints."""

from dataclasses import replace
import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

APP_DIR = Path(__file__).resolve().parents[2]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from backend.config import load_settings  # noqa: E402
from backend.main import create_app  # noqa: E402
from backend.repositories.artifact_store import ArtifactStore  # noqa: E402
from backend.tests.test_unit import FakeNeo4jRepository  # noqa: E402


@pytest.fixture()
def nav_client(tmp_path: Path, monkeypatch) -> TestClient:
    rag_dir = tmp_path / "rag-v1"
    rag_dir.mkdir(parents=True)
    (rag_dir / "research-communities.json").write_text(
        json.dumps(
            {
                "communities": {
                    "research:L1:1": {
                        "community_id": "research:L1:1",
                        "network": "research",
                        "level": 1,
                        "parent_id": None,
                        "size": 12,
                        "paper_count": 40,
                        "papers_by_year": {"2021": 5, "2025": 15},
                        "members": [
                            {"id": "method:Q3621696", "label": "Method", "name": "Large Language Models (LLMs)", "papers": 40}
                        ],
                        "top_entities": [{"id": "method:Q3621696", "label": "Method", "name": "Large Language Models (LLMs)", "papers": 40}],
                        "top_papers": [{"id": "paper:aaai:2024:1", "title": "Sample Paper", "year": 2024, "in_corpus_citations": 5}],
                        "top_organizations": [{"id": "organization:I19820366", "name": "Chinese Academy of Sciences", "papers": 10}],
                        "children": [],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (rag_dir / "community-reports.json").write_text(
        json.dumps(
            {
                "reports": [
                    {
                        "community_id": "research:L1:1",
                        "network": "research",
                        "level": 1,
                        "size": 12,
                        "paper_count": 40,
                        "title": "LLM Reasoning Cluster",
                        "summary": "Large Language Models cluster summary.",
                        "key_findings": [{"claim": "Covers 40 papers.", "paper_ids": ["paper:aaai:2024:1"]}],
                        "centrality_rating": 8,
                        "ai_generated_label": "AI-generated from graph data",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (rag_dir / "entity-descriptions.json").write_text(
        json.dumps(
            {
                "descriptions": [
                    {
                        "id": "method:Q3621696",
                        "label": "Method",
                        "name": "Large Language Models (LLMs)",
                        "description": "Transformer-based foundation language models.",
                        "source_kind": "wikipedia",
                        "provenance_label": "Wikipedia (rev 1)",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (rag_dir / "demo-cache.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-11-25T00:00:00+00:00",
                "demos": [
                    {
                        "demo_id": "demo-01-worked-example",
                        "mode": "auto",
                        "question": "Which organizations collaborating with Tsinghua University increased their share of large-language-model papers after 2022?",
                        "latency_seconds": 1.2,
                        "result": {
                            "mode": "local_multihop",
                            "answer": "Example Partner increased share from 0.1 to 0.5 [paper:aaai:2024:1].",
                            "plan": [{"tool": "find", "args": {"type": "Organization", "text": "Tsinghua University"}}],
                            "steps": [
                                {
                                    "tool": "find",
                                    "rows": [{"id": "organization:I99065089", "name": "Tsinghua University"}],
                                    "evidence_ids": ["organization:I99065089"],
                                }
                            ],
                            "subgraph": {"nodes": [{"id": "organization:I99065089", "label": "Organization", "name": "Tsinghua University"}], "edges": []},
                            "citations": ["paper:aaai:2024:1"],
                            "faithfulness": {"passed": True, "errors": []},
                            "linked": {},
                            "ambiguous": [],
                            "ai_generated_label": "AI-generated from graph data",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    cfg = replace(load_settings(), rag_reports_dir=rag_dir, rag_vectors_sqlite=tmp_path / "absent.sqlite")
    store = ArtifactStore(
        summary_path=cfg.summary_artifact_path,
        analysis_path=cfg.analysis_artifact_path,
        network_views_path=cfg.network_views_path,
        audit_results_path=cfg.audit_results_path,
        graph_artifact_path=Path("/nonexistent/graph.json"),
    )
    app = create_app(cfg, repo=FakeNeo4jRepository(), store=store, background_warmup=False)
    return TestClient(app)


def test_trends_subjects_and_aliases(nav_client: TestClient):
    res = nav_client.get("/api/trends", params={"kind": "Topic", "period": "2021-2025"})
    assert res.status_code == 200
    data = res.json()
    assert "descriptive" in data["classification_note"].lower()
    assert data["period"] == "2021-2025"
    assert len(data["items"]) > 0
    assert len(data["heatmap"]) > 0

    subj_search = nav_client.get("/api/subjects", params={"q": "node classification"})
    assert subj_search.status_code == 200
    s_items = subj_search.json()["items"]
    assert len(s_items) >= 1

    det = nav_client.get("/api/subjects/topic:representation-learning")
    assert det.status_code == 200
    d = det.json()
    assert d["ppr_primary_rank_by"] == "lift"
    assert len(d["top_organizations"]) > 0
    assert "lift" in d["top_organizations"][0]


def test_groups_communities_network_science_and_about(nav_client: TestClient):
    grp = nav_client.get("/api/groups", params={"limit": 10})
    assert grp.status_code == 200
    gd = grp.json()
    assert "State Council" in gd["government_exclusion_note"]
    assert len(gd["organizations"]) == 10
    assert gd["org_anchored_communities"][0]["size_tier"] in {"large", "standard"}

    gdet = nav_client.get("/api/groups/organization:I19820366")
    assert gdet.status_code == 200
    assert gdet.json()["profile"]["name"] == "Chinese Academy of Sciences"

    comm = nav_client.get("/api/communities", params={"source": "research_L1"})
    assert comm.status_code == 200
    cd = comm.json()
    assert len(cd["supernodes"]) == 1
    assert cd["supernodes"][0]["ai_generated_label"] == "AI-generated from graph data"

    members = nav_client.get("/api/communities/research:L1:1/members")
    assert members.status_code == 200
    assert members.json()["total"] == 12 or members.json()["members"][0]["id"] == "method:Q3621696"

    ns = nav_client.get("/api/network-science")
    assert ns.status_code == 200
    nsd = ns.json()
    assert nsd["smallworld"]["networks"]["N1"]["decision"]["small_world_holds"] is True
    assert nsd["ranking"]["N3"]["sparsity_note"]
    assert "igraph average local clustering" in nsd["clustering_definition"]

    ab = nav_client.get("/api/about-data")
    assert ab.status_code == 200
    abd = ab.json()
    assert abd["versions"]["v5_enriched"] == "enriched-cb371912e308"
    assert "not human annotations" in abd["ai_assessment_disclosure"].lower()


def test_node360_explorer_enriched_and_ask_cache_and_sse(nav_client: TestClient):
    n360 = nav_client.get("/api/node360/researcher:openalex:A5017743551")
    assert n360.status_code == 200
    assert n360.json()["name"] == "Bo An"

    sch = nav_client.get("/api/explorer-enriched/schema")
    assert sch.status_code == 200
    assert "Method" in sch.json()["labels"]
    assert len(sch.json()["predicates"]) == 18

    demos = nav_client.get("/api/ask/demos")
    assert demos.status_code == 200
    assert len(demos.json()["demos"]) == 7

    q = "Which organizations collaborating with Tsinghua University increased their share of large-language-model papers after 2022?"
    ask_json = nav_client.post("/api/ask", json={"question": q, "mode": "auto", "stream": False, "use_cache": True})
    assert ask_json.status_code == 200
    body = ask_json.json()
    assert body["from_cache"] is True
    assert body["faithfulness"]["passed"] is True

    ask_sse = nav_client.post("/api/ask", json={"question": q, "mode": "auto", "stream": True, "use_cache": True})
    assert ask_sse.status_code == 200
    assert "text/event-stream" in ask_sse.headers["content-type"]
    assert "event: final" in ask_sse.text

    # Guardrails: /api/paths still enforces 4096 byte limit, /api/ask allows up to 8192
    assert nav_client.post("/api/paths", content=b"x" * 4097).status_code == 413
    assert nav_client.post("/api/ask", content=b"x" * 8193).status_code == 413


def test_hosted_llm_env_config_and_graceful_fallback(tmp_path: Path, monkeypatch, nav_client: TestClient):
    monkeypatch.setenv("EXPLORER_LLM_BASE_URL", "https://openrouter.example.invalid/v1")
    monkeypatch.setenv("EXPLORER_LLM_MODEL", "qwen/qwen3.5-4b")
    monkeypatch.setenv("EXPLORER_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("EXPLORER_LLM_API_KEY_ENV", "TEST_HOSTED_LLM_SECRET")
    monkeypatch.delenv("TEST_HOSTED_LLM_SECRET", raising=False)

    svc = nav_client.app.state.navigator_service if hasattr(nav_client.app.state, "navigator_service") else None
    rag_dir = svc.rag_dir if svc is not None else Path("reports/final-exam/rag-v1")
    cfg = replace(
        load_settings(),
        rag_reports_dir=rag_dir,
        rag_vectors_sqlite=tmp_path / "absent.sqlite",
    )
    store = ArtifactStore(
        summary_path=cfg.summary_artifact_path,
        analysis_path=cfg.analysis_artifact_path,
        network_views_path=cfg.network_views_path,
        audit_results_path=cfg.audit_results_path,
        graph_artifact_path=Path("/nonexistent/graph.json"),
    )
    hosted_client = TestClient(create_app(cfg, repo=FakeNeo4jRepository(), store=store, background_warmup=False))

    about = hosted_client.get("/api/about-data").json()
    assert about["runtime_model"]["model_id"] == "qwen/qwen3.5-4b"
    assert about["runtime_model"]["provider"] == "openrouter"
    assert "TEST_HOSTED_LLM_SECRET" not in json.dumps(about)

    # 1. Scripted demo prompt falls back cleanly to cached trace when API key is missing
    demo_q = "Which organizations collaborating with Tsinghua University increased their share of large-language-model papers after 2022?"
    r_demo = hosted_client.post("/api/ask", json={"question": demo_q, "mode": "auto", "stream": False, "use_cache": False})
    assert r_demo.status_code == 200
    d_body = r_demo.json()
    assert d_body["from_cache"] is True
    assert d_body["fallback_reason"] == "llm_unavailable_served_cached_demo"

    # 2. Custom uncached prompt returns structured non-500 llm_unavailable payload (JSON & SSE)
    r_custom = hosted_client.post("/api/ask", json={"question": "Custom offline test query?", "mode": "auto", "stream": False, "use_cache": False})
    assert r_custom.status_code == 200
    c_body = r_custom.json()
    assert c_body["status"] == "llm_unavailable"
    assert len(c_body["fallback_available_demos"]) == 7

    r_sse = hosted_client.post("/api/ask", json={"question": "Custom offline test query?", "mode": "auto", "stream": True, "use_cache": False})
    assert r_sse.status_code == 200
    assert "llm_unavailable" in r_sse.text
