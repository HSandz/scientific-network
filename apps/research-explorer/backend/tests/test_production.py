"""Production evidence parity and public API guardrails (offline fixtures)."""
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.config import load_settings
from backend.main import create_app
from backend.repositories.artifact_store import ArtifactStore
from backend.tests.test_unit import FakeNeo4jRepository

ROOT = Path(__file__).resolve().parents[4]


def test_sqlite_roundtrip_duplicate_observations_and_all_lookup_keys(tmp_path):
    """Repeated support rows and aligned author-paper-organization triples survive."""
    root = tmp_path / 'repo'
    sources = {
        'data/processed/release-graph-v4/graph.json': {
            'evidence': [{'id': 'ev:1', 'excerpt': 'source text', 'support_edge_ids': ['edge:1'], 'support_paper_ids': ['paper:1']}],
            'affiliation_observations': [
                {'researcher_id': 'researcher:1', 'organization_id': 'organization:1', 'paper_id': 'paper:1', 'raw': 'one'},
                {'researcher_id': 'researcher:1', 'organization_id': 'organization:1', 'paper_id': 'paper:1', 'raw': 'one'},
                {'researcher_id': 'researcher:1', 'organization_id': 'organization:2', 'paper_id': 'paper:1', 'raw': 'two'},
                {'researcher_id': 'researcher:2', 'organization_id': 'organization:1', 'paper_id': 'paper:2', 'raw': 'same name different ID'},
            ]},
        'reports/release-v4/analysis.json': {'projections': {}, 'release_metrics': {}},
        'reports/release-v4/graph-summary.json': {},
        'reports/final-report/network-views-v4-v1/network-views.json': {},
        'reports/release-v4/audit-results-agent-v2.json': {},
        'configs/quality-agent-release-v2.yaml': {},
        'reports/release-v3/topic-eval-agent.json': {},
        'reports/release-v4/historical-topic-reuse-v2.json': {},
    }
    for name, data in sources.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    spec = importlib.util.spec_from_file_location('prepare', ROOT / 'ops/azure/scripts/prepare-artifacts.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / 'artifacts'
    module.build(root, output)
    store = ArtifactStore(summary_path=output/'summary.json', analysis_path=output/'analysis.json', network_views_path=output/'network-views.json', audit_results_path=output/'audit.json', graph_artifact_path=output/'absent.json', ledger_sqlite_path=output/'ledger.sqlite')
    assert store.ledger_available
    assert store.ensure_ledger_loaded()
    assert store.evidence_by_id['ev:1'] == sources['data/processed/release-graph-v4/graph.json']['evidence'][0]
    assert len(store.affiliations_by_researcher_org[('researcher:1', 'organization:1')]) == 2
    assert len(store.affiliations_by_paper['paper:1']) == 3
    assert len(store.affiliations_by_researcher['researcher:1']) == 3
    assert len(store.affiliations_by_org['organization:1']) == 3
    assert store.evidence_by_id.get('absent') is None
    assert store.affiliations_by_paper.get('absent', []) == []
    # Versioned immutable artifacts cannot be accidentally rebuilt in place.
    with pytest.raises(SystemExit):
        module.build(root, output)


def test_public_routes_reject_large_bodies_and_hide_debug_endpoints():
    cfg = replace(load_settings(), production=True)
    app = create_app(cfg, repo=FakeNeo4jRepository(), background_warmup=False)
    with TestClient(app) as client:
        assert client.get('/api/live').status_code == 200
        for path in ('/docs', '/redoc', '/openapi.json'):
            assert client.get(path).status_code == 404
        assert client.post('/api/search', json={}).status_code == 405
        assert client.post('/api/paths', content=b'x'*4097).status_code == 413
        assert client.get('/api/search?q='+'x'*8200).status_code == 414
        assert client.get('/api/search?limit=100000').status_code == 422
        assert client.get('/api/live', headers={'Origin': 'https://evil.example'}).headers.get('access-control-allow-origin') is None


def test_readiness_rechecks_connection_after_inventory_was_verified():
    from types import SimpleNamespace
    from neo4j.exceptions import ServiceUnavailable

    class ReadinessRepo(FakeNeo4jRepository):
        connected = True

        def run_read(self, query):
            if not self.connected:
                raise ServiceUnavailable('simulated outage')
            return [{'ready': 1}]

    store = SimpleNamespace(ledger_available=True, **{name: {'available': True} for name in (
        'summary_data', 'analysis_data', 'network_views_data', 'audit_results_data',
        'quality_config_data', 'topic_eval_data', 'historical_topic_reuse_data',
    )})
    repo = ReadinessRepo()
    app = create_app(load_settings(), repo=repo, store=store)
    with TestClient(app) as client:
        assert client.get('/api/ready').status_code == 200
        repo.connected = False
        assert client.get('/api/ready').status_code == 503
        repo.connected = True
        store.topic_eval_data = {}
        assert client.get('/api/ready').status_code == 503


def test_forwarded_headers_cannot_bypass_rate_limit(monkeypatch):
    monkeypatch.setattr('backend.main.RATE_LIMIT_MAX_REQUESTS', 2)
    app = create_app(load_settings(), repo=FakeNeo4jRepository(), background_warmup=False)
    with TestClient(app) as client:
        assert client.get('/api/live', headers={'X-Forwarded-For': '1.1.1.1'}).status_code == 200
        assert client.get('/api/live', headers={'X-Forwarded-For': '2.2.2.2'}).status_code == 200
        assert client.get('/api/live', headers={'X-Forwarded-For': '3.3.3.3'}).status_code == 429
