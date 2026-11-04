import json
from pathlib import Path

import pytest

from scientific_network.contracts import GraphArtifact

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def graph_payload():
    return json.loads((ROOT / "tests/fixtures/synthetic_graph.json").read_text())


@pytest.fixture
def graph(graph_payload):
    return GraphArtifact.model_validate(graph_payload)
